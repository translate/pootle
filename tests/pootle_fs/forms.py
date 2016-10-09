# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django import forms

from pootle.core.plugin import provider
from pootle_fs.delegate import fs_plugins, fs_url_validator
from pootle_fs.finder import TranslationPathValidator
from pootle_fs.forms import ProjectFSAdminForm


@pytest.mark.django_db
def test_form_fs_project_admin(no_fs_plugins, project0):

    class Dummy1FSPlugin(object):
        fs_type = "dummy1_plugin"
        name = "dummy1"

    class Dummy2FSPlugin(object):
        fs_type = "dummy2_plugin"
        name = "dummy2"

    class DummyURLValidator(object):

        def validate(self, v):
            pass

    @provider(fs_plugins)
    def fs_plugin_provider(**kwargs_):
        return dict(
            dummy1=Dummy1FSPlugin,
            dummy2=Dummy2FSPlugin)

    @provider(fs_url_validator, sender=Dummy2FSPlugin)
    def fs_url_validator_getter(**kwargs_):
        return DummyURLValidator

    project0.config["pootle_fs.fs_type"] = "dummy1_plugin"
    project0.config["pootle_fs.fs_url"] = "/foo/bar"
    project0.config["pootle_fs.translation_paths"] = dict(
        default="/<language_code>/<filename>.<ext>")
    form = ProjectFSAdminForm(
        project=project0,
        data=dict(
            fs_url="/tmp/dummy2",
            fs_type="dummy2",
            translation_path="/some/path/to/<language_code>/<filename>.<ext>"))
    assert form.is_valid()
    assert form.fs_path_validator is TranslationPathValidator
    fs_type_choices = list(
        (plugin_type, plugin.name or plugin.fs_type)
        for plugin_type, plugin
        in fs_plugins.gather().items())
    assert list(form.fs_type_choices) == fs_type_choices
    assert list(form.fields["fs_type"].choices) == fs_type_choices
    assert form.fields["fs_type"].initial == "dummy1_plugin"
    assert form.fields["fs_url"].initial == "/foo/bar"
    assert form.fields["translation_path"].initial == (
        "/<language_code>/<filename>.<ext>")
    assert isinstance(
        form.fs_url_validator, DummyURLValidator)
    form.save()
    assert project0.config["pootle_fs.fs_type"] == "dummy2"
    assert project0.config["pootle_fs.fs_url"] == "/tmp/dummy2"
    assert project0.config["pootle_fs.translation_paths"] == dict(
        default="/some/path/to/<language_code>/<filename>.<ext>")


@pytest.mark.django_db
def test_form_fs_project_bad(no_fs_plugins, project0):

    class Dummy1FSPlugin(object):
        fs_type = "dummy1_plugin"
        name = "dummy1"

    class Dummy2FSPlugin(object):
        fs_type = "dummy2_plugin"
        name = "dummy2"

    class DummyURLValidator(object):

        def validate(self, v):
            if v == "DONT_SET_THIS":
                raise forms.ValidationError("dont set it!")

    @provider(fs_plugins)
    def fs_plugin_provider(**kwargs_):
        return dict(
            dummy1=Dummy1FSPlugin,
            dummy2=Dummy2FSPlugin)

    @provider(fs_url_validator, sender=Dummy2FSPlugin)
    def fs_url_validator_getter(**kwargs_):
        return DummyURLValidator

    form = ProjectFSAdminForm(
        project=project0,
        data={})
    assert not form.is_valid()
    assert (
        sorted(form.errors.keys())
        == ['fs_type', 'fs_url', 'translation_path'])
    form = ProjectFSAdminForm(
        project=project0,
        data=dict(fs_type="DOES_NOT_EXIST"))
    assert not form.is_valid()
    assert (
        sorted(form.errors.keys())
        == ['fs_type', 'fs_url', 'translation_path'])
    form = ProjectFSAdminForm(
        project=project0,
        data=dict(
            fs_type="DOES_NOT_EXIST",
            fs_url="foo/bar"))
    assert not form.is_valid()
    assert sorted(form.errors.keys()) == ["fs_type", "translation_path"]
    form = ProjectFSAdminForm(
        project=project0,
        data=dict(
            translation_path="/good/path/<language_code>/<filename>.<ext>",
            fs_type="dummy2",
            fs_url="DONT_SET_THIS"))
    assert not form.is_valid()
    assert form.errors.keys() == ["fs_url"]
    form = ProjectFSAdminForm(
        project=project0,
        data=dict(
            translation_path="/good/path/<NO_language_code>/<filename>.<ext>",
            fs_type="dummy2",
            fs_url="/good/path"))
    assert not form.is_valid()
    assert form.errors.keys() == ["translation_path"]

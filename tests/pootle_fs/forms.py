# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import sys
from collections import OrderedDict

import pytest

from pytest_pootle.factories import LanguageDBFactory

from django import forms

from pootle.core.delegate import revision
from pootle.core.plugin import provider
from pootle_fs.delegate import fs_plugins, fs_url_validator
from pootle_fs.finder import TranslationMappingValidator
from pootle_fs.forms import LangMappingFormSet, ProjectFSAdminForm
from pootle_language.models import Language


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
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

    project0.config["pootle_fs.fs_type"] = "dummy1_plugin"
    project0.config["pootle_fs.fs_url"] = "/foo/bar"
    project0.config["pootle_fs.translation_mappings"] = dict(
        default="/<language_code>/<filename>.<ext>")

    with no_fs_plugins():
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
            data=dict(
                fs_url="/tmp/dummy2",
                fs_type="dummy2",
                translation_mapping=(
                    "/some/path/to/<language_code>/<filename>.<ext>")))
        assert form.is_valid()
        assert form.fs_path_validator is TranslationMappingValidator
        fs_type_choices = list(
            (plugin_type, plugin.name or plugin.fs_type)
            for plugin_type, plugin
            in fs_plugins.gather().items())
        assert list(form.fs_type_choices) == fs_type_choices
        assert list(form.fields["fs_type"].choices) == fs_type_choices
        assert form.fields["fs_type"].initial == "dummy1_plugin"
        assert form.fields["fs_url"].initial == "/foo/bar"
        assert form.fields["translation_mapping"].initial == (
            "/<language_code>/<filename>.<ext>")
        assert isinstance(
            form.fs_url_validator, DummyURLValidator)
        form.save()
        assert project0.config["pootle_fs.fs_type"] == "dummy2"
        assert project0.config["pootle_fs.fs_url"] == "/tmp/dummy2"
        assert project0.config["pootle_fs.translation_mappings"] == dict(
            default="/some/path/to/<language_code>/<filename>.<ext>")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_form_fs_project_bad(no_fs_plugins, project0):

    with no_fs_plugins():

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
            == ['fs_type', 'fs_url', 'translation_mapping'])
        form = ProjectFSAdminForm(
            project=project0,
            data=dict(fs_type="DOES_NOT_EXIST"))
        assert not form.is_valid()
        assert (
            sorted(form.errors.keys())
            == ['fs_type', 'fs_url', 'translation_mapping'])
        form = ProjectFSAdminForm(
            project=project0,
            data=dict(
                fs_type="DOES_NOT_EXIST",
                fs_url="foo/bar"))
        assert not form.is_valid()
        assert sorted(form.errors.keys()) == ["fs_type", "translation_mapping"]
        form = ProjectFSAdminForm(
            project=project0,
            data=dict(
                translation_mapping="/good/path/<language_code>/<filename>.<ext>",
                fs_type="dummy2",
                fs_url="DONT_SET_THIS"))
        assert not form.is_valid()
        assert form.errors.keys() == ["fs_url"]
        form = ProjectFSAdminForm(
            project=project0,
            data=dict(
                translation_mapping=(
                    "/good/path/<NO_language_code>/<filename>.<ext>"),
                fs_type="dummy2",
                fs_url="/good/path"))
        assert not form.is_valid()
        assert form.errors.keys() == ["translation_mapping"]


def _get_management_data(formset):
    management_form = formset.management_form
    data = {}
    for i in 'TOTAL_FORMS', 'INITIAL_FORMS', 'MIN_NUM_FORMS', 'MAX_NUM_FORMS':
        data['%s-%s' % (management_form.prefix, i)] = management_form[i].value()
    return data


@pytest.mark.django_db
def test_formset_fs_project_lang_mapper(project0, language0, language1):
    formset = LangMappingFormSet(project=project0)
    assert formset.project == project0
    assert not formset.forms[0].fields["pootle_code"].initial
    assert formset.forms[0].initial == {}

    # add a mapping
    data = _get_management_data(formset)
    data["form-0-pootle_code"] = language0.code
    data["form-0-fs_code"] = "FOO"
    formset = LangMappingFormSet(
        project=project0,
        data=data)
    assert formset.is_valid()
    assert formset.forms[0].project == project0
    assert (
        formset.forms[0].cleaned_data
        == dict(remove=False, pootle_code=language0, fs_code="FOO"))
    assert (
        formset.cleaned_mapping
        == OrderedDict([(u'FOO', u'language0')]))
    orig_revision = revision.get(
        formset.project.__class__)(
            formset.project).get(key="pootle.fs.sync")
    formset.save()
    assert (
        orig_revision
        != revision.get(
            formset.project.__class__)(
                formset.project).get(key="pootle.fs.sync"))
    assert (
        project0.config["pootle.core.lang_mapping"]
        == OrderedDict([(u'FOO', u'language0')]))

    # add another mapping
    formset = LangMappingFormSet(project=project0)
    data = _get_management_data(formset)
    assert data['form-INITIAL_FORMS'] == 1
    assert formset.initial == [{'fs_code': u'FOO', 'pootle_code': u'language0'}]
    data["form-0-pootle_code"] = language0.code
    data["form-0-fs_code"] = "FOO"
    data["form-1-pootle_code"] = language1.code
    data["form-1-fs_code"] = "BAR"
    formset = LangMappingFormSet(
        project=project0,
        data=data)
    assert formset.is_valid()
    assert (
        formset.forms[1].cleaned_data
        == dict(remove=False, pootle_code=language1, fs_code="BAR"))
    # language0 is excluded from other fields choices
    assert (
        sorted(
            formset.forms[1].fields[
                "pootle_code"].queryset.values_list("code", flat=True))
        == sorted(
            Language.objects.exclude(
                code=language0.code).values_list("code", flat=True)))
    formset.save()
    assert (
        project0.config["pootle.core.lang_mapping"]
        == OrderedDict([(u'FOO', u'language0'), (u'BAR', 'language1')]))

    # update the first
    formset = LangMappingFormSet(project=project0)
    languageX = LanguageDBFactory()
    data = _get_management_data(formset)
    data["form-0-pootle_code"] = languageX.code
    data["form-0-fs_code"] = "FOO"
    data["form-1-pootle_code"] = language1.code
    data["form-1-fs_code"] = "BAR"
    formset = LangMappingFormSet(
        project=project0,
        data=data)
    assert formset.is_valid()
    assert (
        formset.forms[0].cleaned_data
        == dict(remove=False, pootle_code=languageX, fs_code="FOO"))
    formset.save()
    assert (
        project0.config["pootle.core.lang_mapping"]
        == OrderedDict([(u'FOO', languageX.code), (u'BAR', 'language1')]))

    # remove the second
    formset = LangMappingFormSet(project=project0)
    languageX = LanguageDBFactory()
    data = _get_management_data(formset)
    data["form-0-pootle_code"] = languageX.code
    data["form-0-fs_code"] = "FOO"
    data["form-1-pootle_code"] = language1.code
    data["form-1-fs_code"] = "BAR"
    data["form-1-remove"] = True
    formset = LangMappingFormSet(
        project=project0,
        data=data)
    assert formset.is_valid()
    assert (
        formset.forms[1].cleaned_data
        == dict(remove=True, pootle_code=language1, fs_code="BAR"))
    formset.save()
    assert (
        project0.config["pootle.core.lang_mapping"]
        == OrderedDict([(u'FOO', languageX.code)]))


@pytest.mark.django_db
def test_formset_fs_project_lang_mapper_bad(project0, language0, language1):
    formset = LangMappingFormSet(project=project0)
    assert formset.project == project0
    assert not formset.forms[0].fields["pootle_code"].initial
    assert formset.forms[0].initial == {}

    # add a mapping with bad pootle_code
    data = _get_management_data(formset)
    data["form-0-pootle_code"] = "DOES NOT EXIST"
    data["form-0-fs_code"] = "FOO"
    formset = LangMappingFormSet(
        project=project0,
        data=data)
    assert not formset.is_valid()
    assert not formset.forms[0].is_valid()

    # add a mapping succesfully
    data["form-0-pootle_code"] = language0.code
    data["form-0-fs_code"] = "FOO"
    formset = LangMappingFormSet(
        project=project0,
        data=data)
    formset.save()

    # add a mapping with duplicate pootle_code
    data = _get_management_data(LangMappingFormSet(project=project0))
    data["form-0-pootle_code"] = language0.code
    data["form-0-fs_code"] = "FOO"
    data["form-1-pootle_code"] = language0.code
    data["form-1-fs_code"] = "BAR"
    formset = LangMappingFormSet(
        project=project0,
        data=data)
    assert not formset.is_valid()

    # add a mapping with duplicate fs_code
    data = _get_management_data(LangMappingFormSet(project=project0))
    data["form-0-pootle_code"] = language0.code
    data["form-0-fs_code"] = "FOO"
    data["form-1-pootle_code"] = language1.code
    data["form-1-fs_code"] = "FOO"
    formset = LangMappingFormSet(
        project=project0,
        data=data)
    assert not formset.is_valid()

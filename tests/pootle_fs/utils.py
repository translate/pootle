#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from fnmatch import translate

import pytest

from pytest_pootle.factories import ProjectDBFactory

from pootle.core.exceptions import MissingPluginError, NotConfiguredError
from pootle.core.plugin import provider
from pootle_fs.delegate import fs_plugins
from pootle_fs.models import StoreFS
from pootle_fs.utils import (
    PathFilter, StoreFSPathFilter, StorePathFilter, FSPlugin, parse_fs_url)
from pootle_project.models import Project
from pootle_store.models import Store


class DummyFSPlugin(object):

    def __eq__(self, other):
        return (
            isinstance(other, self.__class__)
            and self.project == other.project)

    def __str__(self):
        return (
            "<%s(%s)>"
            % (self.__class__.__name__, self.project))

    def __init__(self, project):
        self.project = project

    @property
    def plugin_property(self):
        return "Plugin property"

    def plugin_method(self, foo):
        return "Plugin method called with: %s" % foo


@pytest.mark.django_db
def test_store_fs_path_filter_instance():
    path_filter = StoreFSPathFilter()
    assert path_filter.pootle_path is None
    assert path_filter.pootle_regex is None
    assert path_filter.fs_path is None
    assert path_filter.fs_regex is None
    # regexes are cached
    path_filter.pootle_path = "/foo"
    path_filter.fs_path = "/bar"
    assert path_filter.pootle_regex is None
    assert path_filter.fs_regex is None
    del path_filter.__dict__["pootle_regex"]
    del path_filter.__dict__["fs_regex"]
    assert (
        path_filter.pootle_regex
        == path_filter.path_regex(path_filter.pootle_path))
    assert (
        path_filter.fs_regex
        == path_filter.path_regex(path_filter.fs_path))


@pytest.mark.django_db
def test_store_path_filter_instance():
    path_filter = StorePathFilter()
    assert path_filter.pootle_path is None
    assert path_filter.pootle_regex is None
    assert not hasattr(path_filter, "fs_path")
    assert not hasattr(path_filter, "fs_regex")
    # regexes are cached
    path_filter.pootle_path = "/foo"
    path_filter.fs_path = "/bar"
    assert path_filter.pootle_regex is None
    del path_filter.__dict__["pootle_regex"]
    assert (
        path_filter.pootle_regex
        == path_filter.path_regex(path_filter.pootle_path))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "glob", [None, "/language0", "/language0/*", "*.po",
             "/language[01]*", "/language[!1]/*", "/language?/*"])
def test_store_path_filtered(glob):
    project = Project.objects.get(code="project0")
    stores = Store.objects.filter(
        translation_project__project=project)
    path_filter = StorePathFilter(glob)
    if not glob:
        assert path_filter.filtered(stores) is stores
    else:
        assert (
            list(path_filter.filtered(stores))
            == list(stores.filter(pootle_path__regex=path_filter.pootle_regex)))


@pytest.mark.django_db
@pytest.mark.parametrize(
    "glob", [None, "/language0", "/language0/*", "*.po",
             "/language[01]*", "/language[!1]/*", "/language?/*"])
def test_store_fs_path_filtered(glob):
    project = Project.objects.get(code="project0")
    stores = Store.objects.filter(
        translation_project__project=project)
    for store in stores:
        StoreFS.objects.create(
            store=store,
            path="/fs%s" % store.pootle_path)
    stores_fs = StoreFS.objects.filter(project=project)
    if not glob:
        assert StoreFSPathFilter().filtered(stores_fs) is stores_fs
    else:
        path_filter = StoreFSPathFilter(pootle_path=glob)
        assert (
            list(path_filter.filtered(stores_fs))
            == list(stores_fs.filter(pootle_path__regex=path_filter.pootle_regex)))
        path_filter = StoreFSPathFilter(fs_path="/fs%s" % glob)
        assert (
            list(path_filter.filtered(stores_fs))
            == list(stores_fs.filter(path__regex=path_filter.fs_regex)))


@pytest.mark.parametrize(
    "glob", ["/foo", "/bar/*", "*.baz", "[abc]", "[!xyz]", "language?"])
def test_fs_path_filter_path_regex(glob):
    assert (
        PathFilter().path_regex(glob)
        == translate(glob).replace("\Z(?ms)", "$"))


@pytest.mark.django_db
def test_project_fs_instance():

    @provider(fs_plugins, sender=Project)
    def provide_fs_plugin(**kwargs):
        return dict(dummyfs=DummyFSPlugin)

    project = Project.objects.get(code="project0")
    project.config["pootle_fs.fs_type"] = "dummyfs"
    project.config["pootle_fs.fs_url"] = "/foo/bar"
    plugin = FSPlugin(project)
    assert str(plugin) == "<DummyFSPlugin(Project 0)>"
    assert plugin.project == project
    assert plugin.plugin_property == "Plugin property"
    assert plugin.plugin_method("bar") == "Plugin method called with: bar"
    assert plugin == FSPlugin(project)


@pytest.mark.django_db
def test_project_fs_instance_bad(english):

    # needs a Project
    with pytest.raises(TypeError):
        FSPlugin()
    project = ProjectDBFactory(source_language=english)
    # project is not configured
    with pytest.raises(NotConfiguredError):
        FSPlugin(project)
    project.config["pootle_fs.fs_type"] = "foo"
    with pytest.raises(NotConfiguredError):
        FSPlugin(project)
    project.config["pootle_fs.fs_type"] = None
    project.config["pootle_fs.fs_url"] = "bar"
    with pytest.raises(NotConfiguredError):
        FSPlugin(project)
    project.config["pootle_fs.fs_type"] = "foo"
    with pytest.raises(MissingPluginError):
        FSPlugin(project)

    @provider(fs_plugins, sender=Project)
    def provide_fs_plugin(**kwargs):
        return dict(dummyfs=DummyFSPlugin)

    with pytest.raises(MissingPluginError):
        FSPlugin(project)


@pytest.mark.parametrize(
    "fs, fs_type, fs_url", [
        ("/test/fs/path/", "localfs", "/test/fs/path/"),
        ("localfs+/test/fs/path/", "localfs", "/test/fs/path/"),
    ])
def test_parse_fs_url(fs, fs_type, fs_url):
    assert (fs_type, fs_url) == parse_fs_url(fs)

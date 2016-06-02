# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
from fnmatch import fnmatch

import pytest

from django.db.models import Q
from django.utils.functional import cached_property


FS_PATH_QS = OrderedDict((
    ("all", (
        (None, None, None))),
    ("language0", (
        (Q(pootle_path__startswith="/language0"),
         "/language0/*", None))),
    ("fs/language1", (
        (Q(pootle_path__startswith="/language1"),
         None, "/fs/language1/*"))),
    ("store0.po", (
        (Q(pootle_path__endswith="store0.po"),
         "*/store0.po", "*/store0.po"))),
    ("none", (
        (False, "/language0/*", "/fs/language1/*")))))


class DummyPlugin(object):

    @property
    def file_class(self):
        from pootle_fs.files import FSFile

        return FSFile

    def __str__(self):
        return "<DummyPlugin(%s)>" % self.project

    def __init__(self, project):
        self.project = project

    def find_translations(self, fs_path=None, pootle_path=None):
        for pp in self.resources.stores.values_list("pootle_path", flat=True):
            if pootle_path and not fnmatch(pp, pootle_path):
                continue
            fp = self.get_fs_path(pp)
            if fs_path and not fnmatch(fp, fs_path):
                continue
            yield pp, fp

    @cached_property
    def resources(self):
        from pootle_fs.resources import FSProjectResources

        return FSProjectResources(self.project)

    def get_fs_path(self, pootle_path):
        return "/fs%s" % pootle_path


@pytest.fixture
def project0_dummy_plugin(settings, request, no_fs_plugins, no_fs_files):
    from pootle.core.plugin import getter, provider
    from pootle_fs.delegate import fs_file, fs_plugins
    from pootle_fs.files import FSFile
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project

    @provider(fs_plugins, weak=False)
    def plugin_provider(**kwargs):
        return dict(dummyfs=DummyPlugin)

    @getter(fs_file, weak=False, sender=DummyPlugin)
    def fs_files_getter(**kwargs):
        return FSFile

    project = Project.objects.get(code="project0")
    settings.POOTLE_FS_PATH = "/tmp/foo/"
    project.config["pootle_fs.fs_type"] = "dummyfs"
    project.config["pootle_fs.fs_url"] = "/foo/bar"
    return FSPlugin(project)


@pytest.fixture(params=FS_PATH_QS.keys())
def fs_path_queries(project0_dummy_plugin, request):
    return project0_dummy_plugin, FS_PATH_QS[request.param]


@pytest.fixture(params=FS_PATH_QS.keys())
def fs_path_qs(request):
    return FS_PATH_QS[request.param]


@pytest.fixture
def project0_dummy_plugin_fs_changed(settings, request,
                                     no_fs_plugins, no_fs_files):
    from pootle.core.plugin import getter, provider
    from pootle_fs.delegate import fs_file, fs_plugins
    from pootle_fs.files import FSFile
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project

    class FSChangedFile(FSFile):

        @property
        def fs_changed(self):
            return True

    class PootleConflictDummyPlugin(DummyPlugin):

        pass

    @provider(fs_plugins, weak=False, sender=Project)
    def plugin_provider(**kwargs):
        return dict(dummyfs=PootleConflictDummyPlugin)

    @getter(fs_file, weak=False, sender=PootleConflictDummyPlugin)
    def fs_files_getter(**kwargs):
        return FSChangedFile

    project = Project.objects.get(code="project0")
    settings.POOTLE_FS_PATH = "/tmp/foo/"
    project.config["pootle_fs.fs_type"] = "dummyfs"
    project.config["pootle_fs.fs_url"] = "/foo/bar"

    return FSPlugin(project)


@pytest.fixture
def project0_dummy_plugin_no_stores(settings, request,
                                    no_fs_plugins, no_fs_files):
    from pytest_pootle.utils import add_store_fs

    from pootle.core.plugin import getter, provider
    from pootle_fs.delegate import fs_file, fs_plugins
    from pootle_fs.files import FSFile
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project
    from pootle_store.models import Store

    settings.POOTLE_FS_PATH = "/tmp/foo/"
    project = Project.objects.get(code="project0")
    project.config["pootle_fs.fs_type"] = "dummyfs"
    project.config["pootle_fs.fs_url"] = "/foo/bar"
    stores = Store.objects.filter(
        translation_project__project=project)
    pootle_paths = list(stores.values_list("pootle_path", flat=True))

    class NoStoresDummyPlugin(DummyPlugin):

        def find_translations(self, fs_path=None, pootle_path=None):
            for pp in pootle_paths:
                if pootle_path and not fnmatch(pp, pootle_path):
                    continue
                fp = self.get_fs_path(pp)
                if fs_path and not fnmatch(fp, fs_path):
                    continue
                yield pp, fp

    @provider(fs_plugins, weak=False, sender=Project)
    def plugin_provider(**kwargs):
        return dict(dummyfs=NoStoresDummyPlugin)

    @getter(fs_file, weak=False, sender=NoStoresDummyPlugin)
    def fs_files_getter(**kwargs):
        return FSFile

    plugin = FSPlugin(project)
    for store in stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
    return plugin


@pytest.fixture
def project0_dummy_plugin_del_stores(project0_dummy_plugin_no_stores):
    project0_dummy_plugin_no_stores.resources.stores.delete()
    return project0_dummy_plugin_no_stores


@pytest.fixture
def project0_dummy_plugin_obs_stores(project0_dummy_plugin_no_stores):
    for store in project0_dummy_plugin_no_stores.resources.stores:
        store.makeobsolete()
    return project0_dummy_plugin_no_stores


@pytest.fixture
def project0_dummy_plugin_no_files(settings, request,
                                   no_fs_plugins, no_fs_files):
    from pootle.core.plugin import getter, provider
    from pootle_fs.delegate import fs_file, fs_plugins
    from pootle_fs.files import FSFile
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project

    settings.POOTLE_FS_PATH = "/tmp/foo/"

    class NoFilesDummyPlugin(DummyPlugin):

        def find_translations(self, fs_path=None, pootle_path=None):
            return []

    @provider(fs_plugins, weak=False, sender=Project)
    def plugin_provider(**kwargs):
        return dict(dummyfs=NoFilesDummyPlugin)

    @getter(fs_file, weak=False, sender=NoFilesDummyPlugin)
    def fs_files_getter(**kwargs):
        return FSFile

    project = Project.objects.get(code="project0")
    project.config["pootle_fs.fs_type"] = "dummyfs"
    project.config["pootle_fs.fs_url"] = "/foo/bar"

    return FSPlugin(project)

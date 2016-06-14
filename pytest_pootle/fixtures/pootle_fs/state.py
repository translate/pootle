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
         None, "*language1/*"))),
    ("store0.po", (
        (Q(pootle_path__endswith="store0.po"),
         "*/store0.po", "*/store0.po"))),
    ("none", (
        (False, "/language0/*", "/fs/language1/*")))))


def pytest_generate_tests(metafunc):
    from pootle_fs.response import FS_RESPONSE
    from pootle_fs.state import FS_STATE

    if 'fs_responses' in metafunc.fixturenames:
        metafunc.parametrize("fs_responses", FS_RESPONSE)

    if 'fs_states' in metafunc.fixturenames:
        metafunc.parametrize("fs_states", FS_STATE)


class DummyPlugin(object):

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
        from pootle.core.url_helpers import split_pootle_path

        lang_code, proj_code, dir_path, fn = split_pootle_path(pootle_path)
        parts = ["", lang_code]
        if dir_path:
            parts.append(dir_path.rstrip("/"))
        parts.append(fn)
        return "/".join(parts)


@pytest.fixture
def dummyfs(settings, no_fs_plugins, no_fs_files):
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
    return FSPlugin(project)


@pytest.fixture
def dummyfs_untracked(dummyfs):
    dummyfs.resources.tracked.delete()
    return dummyfs


@pytest.fixture(params=FS_PATH_QS.keys())
def fs_path_qs(request):
    return FS_PATH_QS[request.param]


@pytest.fixture
def dummyfs_plugin_fs_changed(settings, no_fs_plugins, no_fs_files):
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
    return FSPlugin(project)


@pytest.fixture
def dummyfs_plugin_no_stores(settings, no_fs_plugins, no_fs_files):
    from pootle.core.plugin import getter, provider
    from pootle_fs.delegate import fs_file, fs_plugins
    from pootle_fs.files import FSFile
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project
    from pootle_store.models import Store

    settings.POOTLE_FS_PATH = "/tmp/foo/"
    project = Project.objects.get(code="project0")
    project.config["pootle_fs.fs_type"] = "dummyfs"
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
    return plugin


@pytest.fixture
def dummyfs_plugin_del_stores(dummyfs_plugin_no_stores):
    dummyfs_plugin_no_stores.resources.stores.delete()
    return dummyfs_plugin_no_stores


@pytest.fixture
def dummyfs_plugin_obs_stores(dummyfs_plugin_no_stores):
    for store in dummyfs_plugin_no_stores.resources.stores:
        store.makeobsolete()
    return dummyfs_plugin_no_stores


@pytest.fixture
def dummyfs_plugin_no_files(settings, no_fs_plugins, no_fs_files):
    from pootle.core.plugin import provider
    from pootle_fs.delegate import fs_plugins
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project

    settings.POOTLE_FS_PATH = "/tmp/foo/"

    class NoFilesDummyPlugin(DummyPlugin):

        def find_translations(self, fs_path=None, pootle_path=None):
            return []

    @provider(fs_plugins, weak=False, sender=Project)
    def plugin_provider(**kwargs):
        return dict(dummyfs=NoFilesDummyPlugin)

    project = Project.objects.get(code="project0")
    project.config["pootle_fs.fs_type"] = "dummyfs"
    plugin = FSPlugin(project)
    return plugin

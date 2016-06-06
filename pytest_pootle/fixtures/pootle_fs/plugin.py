# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil
from fnmatch import fnmatch
from uuid import uuid4

import pytest


_plugin_fetch_base = {
    'conflict': 1,
    'conflict_untracked': 1,
    'fs_ahead': 1,
    'fs_removed': 1,
    'fs_untracked': 2,
    'pootle_ahead': 1,
    'pootle_removed': 1,
    'pootle_untracked': 1}


@pytest.fixture
def localfs(settings, project_fs):
    plugin = project_fs
    project = project_fs.project
    project.treestyle = "none"
    project.save()
    project_src = os.path.join(
        settings.POOTLE_TRANSLATION_DIRECTORY, project.code)
    shutil.rmtree(plugin.fs_url)
    shutil.copytree(project_src, plugin.fs_url)
    plugin.project.config["pootle_fs.translation_paths"] = {
        "default": "/<language_code>/<dir_path>/<filename>.<ext>"}
    return plugin


@pytest.fixture
def project0_dummy_finder(no_fs_finder, localfs):
    from pootle.core.plugin import getter
    from pootle.core.url_helpers import split_pootle_path
    from pootle_fs.delegate import fs_finder
    from pootle_fs.finder import TranslationFileFinder
    from pootle_store.models import Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)
    pootle_paths = list(stores.values_list("pootle_path", flat=True))

    class DummyFSFinder(TranslationFileFinder):

        def find(self):
            for pootle_path in pootle_paths:
                fs_path = plugin.get_fs_path(pootle_path)
                if self.path_filters:
                    if not fnmatch(fs_path, self.path_filters[0]):
                        continue
                matched = dict()
                (matched['language_code'],
                 __,
                 matched['dir_path'],
                 matched['filename']) = split_pootle_path(pootle_path)
                matched["ext"] = "po"
                matched['filename'] = os.path.splitext(matched["filename"])[0]
                yield plugin.get_fs_path(pootle_path), matched

    @getter(fs_finder, sender=plugin.__class__, weak=False)
    def get_fs_finder(**kwargs):
        return DummyFSFinder


@pytest.fixture
def project_empty_dummy_finder(no_fs_finder, localfs, project_fs_empty):
    from pootle.core.plugin import getter
    from pootle.core.url_helpers import split_pootle_path
    from pootle_fs.delegate import fs_finder
    from pootle_fs.finder import TranslationFileFinder
    from pootle_store.models import Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)
    pootle_paths = list(stores.values_list("pootle_path", flat=True))

    class DummyEmptyFSFinder(TranslationFileFinder):

        def find(self):
            for pootle_path in pootle_paths:
                pootle_path = pootle_path.replace(
                    plugin.project.code, project_fs_empty.project.code)
                fs_path = plugin.get_fs_path(pootle_path)
                if self.path_filters:
                    if not fnmatch(fs_path, self.path_filters[0]):
                        continue
                matched = dict()
                (matched['language_code'],
                 __,
                 matched['dir_path'],
                 matched['filename']) = split_pootle_path(pootle_path)
                matched["ext"] = "po"
                matched['filename'] = os.path.splitext(matched["filename"])[0]
                yield plugin.get_fs_path(pootle_path), matched

    @getter(fs_finder, sender=plugin.__class__, weak=False)
    def get_fs_finder(**kwargs):
        return DummyEmptyFSFinder


@pytest.fixture
def project0_dummy_finder_empty(no_fs_finder, localfs):
    from pootle.core.plugin import getter
    from pootle_fs.delegate import fs_finder
    from pootle_fs.finder import TranslationFileFinder

    plugin = localfs

    class DummyEmptyFSFinder(TranslationFileFinder):

        def find(self):
            return []

    @getter(fs_finder, sender=plugin.__class__, weak=False)
    def get_fs_finder(**kwargs):
        return DummyEmptyFSFinder


@pytest.fixture
def project0_dummy_storefs_file(no_fs_files, localfs):
    from pootle.core.plugin import getter
    from pootle_fs.delegate import fs_file
    from pootle_fs.files import FSFile

    plugin = localfs

    class DummyFSFile(FSFile):

        _added = False
        _deleted = False
        _fetched = False
        _merged = False
        _pulled = False
        _pushed = False
        _removed = False
        _synced = False

        on_sync = lambda self: setattr(self, "_synced", True)

        @property
        def latest_hash(self):
            return str(hash(self.pootle_path))

        def add(self):
            self._added = True

        def delete(self):
            self._deleted = True

        def fetch(self):
            self._fetched = True

        def merge(self, pootle_wins):
            self._merged = True
            if pootle_wins:
                self._merge_pootle = True
            else:
                self._merge_fs = True

        def pull(self, **kwargs):
            self._pulled = True
            self._pull_data = sorted(kwargs.items())

        def push(self):
            self._pushed = True

        def rm(self):
            self._removed = True

    @getter(fs_file, sender=plugin.__class__, weak=False)
    def get_fs_file(**kwargs):
        return DummyFSFile


@pytest.fixture
def localfs_pootle_untracked(settings, tmpdir, project0_dummy_storefs_file):
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project

    project = Project.objects.get(code="project0")
    project.config["pootle_fs.fs_type"] = "localfs"
    new_url = os.path.join(str(tmpdir), "__src__")
    project.config["pootle_fs.fs_url"] = new_url
    plugin = FSPlugin(project)
    plugin.project.config["pootle_fs.translation_paths"] = {
        "default": "/<language_code>/<dir_path>/<filename>.<ext>"}
    settings.POOTLE_FS_PATH = str(tmpdir)
    return plugin


@pytest.fixture
def localfs_fs_removed(settings, tmpdir, project0_dummy_storefs_file):
    from pytest_pootle.utils import add_store_fs

    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project
    from pootle_store.models import Store

    project = Project.objects.get(code="project0")
    project.config["pootle_fs.fs_type"] = "localfs"
    new_url = os.path.join(str(tmpdir), "__src__")
    project.config["pootle_fs.fs_url"] = new_url
    plugin = FSPlugin(project)
    plugin.project.config["pootle_fs.translation_paths"] = {
        "default": "/<language_code>/<dir_path>/<filename>.<ext>"}
    settings.POOTLE_FS_PATH = str(tmpdir)
    stores = Store.objects.filter(
        translation_project__project=plugin.project)
    for store in stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
    return plugin


@pytest.fixture
def localfs_conflict(localfs, project0_dummy_finder,
                     project0_dummy_storefs_file):
    from pytest_pootle.utils import add_store_fs

    from pootle_store.models import Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)

    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))
        store_fs.last_sync_revision = store.get_max_unit_revision() - 1
        store_fs.last_sync_hash = uuid4().hex
        store_fs.save()
    assert len(plugin.state()["conflict"]) == stores.count()
    return plugin


@pytest.fixture
def project0_fs_conflict_untracked(localfs, project0_dummy_finder,
                                   project0_dummy_storefs_file):
    from pootle_store.models import Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)
    pootle_paths = list(stores.values_list("pootle_path", flat=True))
    assert len(plugin.state()["conflict_untracked"]) == len(pootle_paths)
    return plugin


@pytest.fixture
def localfs_pootle_removed(project_fs, project_fs_empty,
                           project_empty_dummy_finder,
                           project0_dummy_storefs_file):
    from pootle.core.models import Revision
    from pootle_fs.models import StoreFS
    from pootle_store.models import Store

    plugin = project_fs_empty
    plugin.project.config["pootle_fs.translation_paths"] = {
        "default": "/<language_code>/<dir_path>/<filename>.<ext>"}
    stores = Store.objects.filter(translation_project__project=project_fs.project)
    max_revision = Revision.get()
    for store in stores:
        pootle_path = store.pootle_path.replace(
            project_fs.project.code, plugin.project.code)
        fs_path = plugin.get_fs_path(pootle_path)
        store_fs = StoreFS.objects.create(
            project=plugin.project,
            path=fs_path,
            pootle_path=pootle_path,
            last_sync_revision=max_revision)
        store_fs.last_sync_hash = store_fs.file.latest_hash
        store_fs.save()
    assert plugin.state()["pootle_removed"]
    assert len(plugin.state()["pootle_removed"]) == stores.count()
    return plugin


@pytest.fixture
def localfs_fs_untracked(project0_dummy_finder,
                         project0_dummy_storefs_file,
                         project_fs_empty):
    plugin = project_fs_empty
    plugin.project.config["pootle_fs.translation_paths"] = {
        "default": "/<language_code>/<dir_path>/<filename>.<ext>"}
    assert plugin.state()["fs_untracked"]
    assert (
        len(plugin.state()["fs_untracked"])
        == len(list(plugin.find_translations())))
    return plugin


@pytest.fixture
def localfs_merge_pootle_wins(localfs, project0_dummy_finder,
                              project0_dummy_storefs_file):

    from pytest_pootle.utils import add_store_fs

    from pootle_store.models import POOTLE_WINS, Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)

    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
        store_fs.resolve_conflict = POOTLE_WINS
        store_fs.staged_for_merge = True
        store_fs.save()
    assert plugin.state()["merge_pootle_wins"]
    assert len(plugin.state()["merge_pootle_wins"]) == stores.count()
    return plugin


@pytest.fixture
def localfs_merge_fs_wins(localfs, project0_dummy_finder,
                          project0_dummy_storefs_file):

    from pytest_pootle.utils import add_store_fs

    from pootle_store.models import FILE_WINS, Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)

    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
        store_fs.resolve_conflict = FILE_WINS
        store_fs.staged_for_merge = True
        store_fs.save()
    assert plugin.state()["merge_fs_wins"]
    assert len(plugin.state()["merge_fs_wins"]) == stores.count()
    return plugin


@pytest.fixture
def localfs_fs_ahead(localfs, request,
                     project0_dummy_finder,
                     project0_dummy_storefs_file):

    from pytest_pootle.utils import add_store_fs

    from pootle_store.models import Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)

    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))
        store_fs.last_sync_revision = store.get_max_unit_revision()
        store_fs.last_sync_hash = uuid4().hex
        store_fs.save()
    assert plugin.state()["fs_ahead"]
    assert len(plugin.state()["fs_ahead"]) == stores.count()
    return plugin


@pytest.fixture
def localfs_fs_staged(project0_dummy_finder,
                      project0_dummy_storefs_file,
                      project_fs_empty):
    from pootle_fs.models import StoreFS

    plugin = project_fs_empty
    plugin.project.config["pootle_fs.translation_paths"] = {
        "default": "/<language_code>/<dir_path>/<filename>.<ext>"}
    matches = list(plugin.find_translations())
    for pootle_path, fs_path in matches:
        StoreFS.objects.create(path=fs_path, pootle_path=pootle_path)
    assert plugin.state()["fs_staged"]
    assert len(plugin.state()["fs_staged"]) == len(matches)
    return plugin


@pytest.fixture
def localfs_pootle_ahead(localfs,
                         project0_dummy_finder,
                         project0_dummy_storefs_file):

    from pytest_pootle.utils import add_store_fs

    from pootle_store.models import Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)

    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))
        store_fs.last_sync_hash = store_fs.file.latest_hash
        store_fs.last_sync_revision = store.get_max_unit_revision()
        store_fs.save()
        unit = store.units.first()
        unit.target = "%sFOO" % store.name
        unit.save()
    assert plugin.state()["pootle_ahead"]
    assert len(plugin.state()["pootle_ahead"]) == stores.count()
    return plugin


@pytest.fixture
def localfs_pootle_staged(project0_dummy_finder_empty,
                          project0_dummy_storefs_file,
                          localfs):
    from pytest_pootle.utils import add_store_fs

    from pootle_store.models import Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)

    for store in stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))

    assert plugin.state()["pootle_staged"]
    assert len(plugin.state()["pootle_staged"]) == len(stores)
    return plugin


@pytest.fixture
def localfs_remove(project0_dummy_finder_empty,
                   project0_dummy_storefs_file,
                   localfs):
    from pytest_pootle.utils import add_store_fs

    from pootle_store.models import Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)
    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))
        store_fs.staged_for_removal = True
        store_fs.save()
    assert plugin.state()["remove"]
    assert len(plugin.state()["remove"]) == len(stores)
    return plugin


@pytest.fixture
def localfs_pootle_staged_real(localfs):
    from pytest_pootle.utils import add_store_fs

    from pootle_store.models import Store

    plugin = localfs
    stores = Store.objects.filter(translation_project__project=plugin.project)

    for store in stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))

    assert plugin.state()["pootle_staged"]
    assert len(plugin.state()["pootle_staged"]) == len(stores)
    return plugin

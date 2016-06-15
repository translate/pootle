# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil

import pytest

from pytest_pootle.fs.utils import parse_fs_action_args


_plugin_fetch_base = {
    'conflict': 1,
    'conflict_untracked': 1,
    'fs_ahead': 1,
    'fs_removed': 1,
    'fs_untracked': 2,
    'pootle_ahead': 1,
    'pootle_removed': 1,
    'pootle_untracked': 1}

RESPONSE_MAP = {
    "conflict": dict(
        add_force=("added_from_pootle", "pootle_staged"),
        fetch_force=("fetched_from_fs", "fs_staged"),
        merge_fs=("staged_for_merge_fs", "merge_fs_wins"),
        merge_pootle=("staged_for_merge_pootle", "merge_pootle_wins")),
    "conflict_untracked": dict(
        add_force=("added_from_pootle", "pootle_staged"),
        fetch_force=("fetched_from_fs", "fs_staged"),
        merge_fs=("staged_for_merge_fs", "merge_fs_wins"),
        merge_pootle=("staged_for_merge_pootle", "merge_pootle_wins"),
        rm_force=("staged_for_removal", "remove")),
    "fs_ahead": dict(
        sync=("pulled_to_pootle", None)),
    "fs_removed": dict(
        add_force=("added_from_pootle", "pootle_staged"),
        rm=("staged_for_removal", "remove")),
    "fs_staged": dict(
        sync=("pulled_to_pootle", None)),
    "fs_untracked": dict(
        fetch=("fetched_from_fs", "fs_staged"),
        rm_force=("staged_for_removal", "remove")),
    "merge_fs_wins": dict(
        sync=("merged_from_fs", None)),
    "merge_pootle_wins": dict(
        sync=("merged_from_pootle", None)),
    "pootle_ahead": dict(
        sync=("pushed_to_fs", None)),
    "pootle_removed": dict(
        fetch_force=("fetched_from_fs", "fs_staged"),
        rm=("staged_for_removal", "remove"),
        rm_force=("staged_for_removal", "remove")),
    "pootle_staged": dict(
        sync=("pushed_to_fs", None)),
    "pootle_untracked": dict(
        add=("added_from_pootle", "pootle_staged"),
        add_force=("added_from_pootle", "pootle_staged"),
        rm_force=("staged_for_removal", "remove")),
    "remove": dict(
        sync=("removed", None))}


def _possible_actions():
    actions = set()
    for state in RESPONSE_MAP:
        actions.update(RESPONSE_MAP[state].keys())
    return actions


def pytest_generate_tests(metafunc):

    if 'localfs_envs' in metafunc.fixturenames:

        from pootle_fs.state import FS_STATE
        env_names = [e for e in FS_STATE.keys() if e not in ["both_removed"]]
        metafunc.parametrize("localfs_env_names", env_names)

    if "possible_action_keys" in metafunc.fixturenames:
        metafunc.parametrize("possible_action_keys", _possible_actions())


@pytest.fixture
def fs_response_map():
    return RESPONSE_MAP


@pytest.fixture
def possible_actions(possible_action_keys):
    return (
        (possible_action_keys, )
        + parse_fs_action_args(possible_action_keys))


@pytest.fixture
def localfs_envs(request, localfs_env_names):
    return (
        localfs_env_names,
        request.getfuncargvalue(
            "localfs_%s" % localfs_env_names))


@pytest.fixture(params=["force_added", "force_fetched"])
def localfs_staged_envs(request):
    return (
        request.param,
        request.getfuncargvalue(
            "localfs_%s" % request.param))


@pytest.fixture
def localfs_env(settings, project_fs):
    return project_fs


@pytest.fixture
def localfs_base(settings, localfs_env):
    localfs_env.resources.tracked.delete()
    shutil.rmtree(localfs_env.fs_url)
    shutil.copytree(
        os.path.join(
            settings.POOTLE_TRANSLATION_DIRECTORY,
            localfs_env.project.code),
        localfs_env.fs_url)
    return localfs_env


@pytest.fixture
def localfs_dummy_finder(no_fs_finder, localfs_env):
    from pootle.core.plugin import getter
    from pootle.core.url_helpers import split_pootle_path
    from pootle_fs.delegate import fs_finder
    from pootle_fs.finder import TranslationFileFinder

    plugin = localfs_env
    stores = plugin.resources.stores
    pootle_paths = list(stores.values_list("pootle_path", flat=True))

    class DummyFSFinder(TranslationFileFinder):

        def find(self):
            for pootle_path in pootle_paths:
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
def localfs_dummy_finder_empty(no_fs_finder, localfs_env):
    from pootle.core.plugin import getter
    from pootle_fs.delegate import fs_finder
    from pootle_fs.finder import TranslationFileFinder

    plugin = localfs_env

    class DummyEmptyFSFinder(TranslationFileFinder):

        def find(self):
            return []

    @getter(fs_finder, sender=plugin.__class__, weak=False)
    def get_fs_finder(**kwargs):
        return DummyEmptyFSFinder


@pytest.fixture
def localfs_dummy_file(no_fs_files):
    from pootle.core.plugin import getter
    from pootle_fs.delegate import fs_file
    from pootle_fs.files import FSFile
    from pootle_fs.localfs import LocalFSPlugin

    class DummyFSFile(FSFile):

        _added = False
        _deleted = False
        _fetched = False
        _merged = False
        _pulled = False
        _pushed = False
        _removed = False
        _synced = False
        _unstaged = False

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

        def unstage(self):
            self._unstaged = True

    @getter(fs_file, sender=LocalFSPlugin, weak=False)
    def get_fs_file(**kwargs):
        return DummyFSFile


@pytest.fixture
def localfs(localfs_env, localfs_dummy_file):
    return localfs_env


@pytest.fixture
def localfs_no_storefs(localfs):
    localfs.resources.tracked.delete()
    return localfs


@pytest.fixture
def localfs_pootle_untracked(localfs_no_storefs):
    plugin = localfs_no_storefs
    stores = plugin.resources.stores
    state = plugin.state()
    assert len(state["pootle_untracked"]) == stores.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_fs_removed(localfs):
    plugin = localfs
    state = plugin.state()
    assert len(state["fs_removed"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_conflict(localfs, localfs_dummy_finder):
    plugin = localfs
    for store_fs in plugin.resources.tracked:
        store_fs.last_sync_revision = store_fs.last_sync_revision - 1
        store_fs.save()
    state = plugin.state()
    assert len(state["conflict"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_conflict_untracked(localfs_no_storefs, localfs_dummy_finder):
    plugin = localfs_no_storefs
    stores = plugin.resources.stores
    pootle_paths = list(stores.values_list("pootle_path", flat=True))
    state = plugin.state()
    assert len(state["conflict_untracked"]) == len(pootle_paths)
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_pootle_removed(localfs, localfs_dummy_finder):
    plugin = localfs
    plugin.resources.stores.delete()
    for store_fs in plugin.resources.tracked:
        store_fs.last_sync_hash = store_fs.file.latest_hash
        store_fs.save()
    state = plugin.state()
    assert len(state["pootle_removed"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_fs_untracked(localfs_base, localfs_dummy_finder, localfs_dummy_file):
    plugin = localfs_base
    plugin.resources.stores.delete()
    state = plugin.state()
    assert len(state["fs_untracked"]) == len(list(plugin.find_translations()))
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_merge_pootle_wins(localfs, localfs_dummy_finder):
    from pootle_store.models import POOTLE_WINS

    plugin = localfs
    plugin.resources.tracked.update(
        resolve_conflict=POOTLE_WINS,
        staged_for_merge=True)
    state = plugin.state()
    assert len(state["merge_pootle_wins"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_merge_fs_wins(localfs, localfs_dummy_finder):
    from pootle_store.models import FILE_WINS

    plugin = localfs

    stores = plugin.resources.stores
    plugin.resources.tracked.update(
        resolve_conflict=FILE_WINS,
        staged_for_merge=True)
    state = plugin.state()
    assert len(state["merge_fs_wins"]) == stores.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_fs_ahead(localfs, localfs_dummy_finder):
    plugin = localfs
    state = plugin.state()
    assert len(state["fs_ahead"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_fs_staged(localfs, localfs_dummy_finder):
    plugin = localfs
    plugin.resources.stores.delete()
    plugin.resources.tracked.update(
        last_sync_hash=None,
        last_sync_revision=None)
    state = plugin.state()
    assert len(state["fs_staged"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_pootle_ahead(localfs, localfs_dummy_finder):
    plugin = localfs
    for store_fs in plugin.resources.tracked:
        store_fs.last_sync_hash = store_fs.file.latest_hash
        store_fs.last_sync_revision = store_fs.last_sync_revision - 1
        store_fs.save()
    state = plugin.state()
    assert len(state["pootle_ahead"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_pootle_staged(localfs, localfs_dummy_finder_empty):
    plugin = localfs
    plugin.resources.tracked.update(
        last_sync_hash=None,
        last_sync_revision=None)
    state = plugin.state()
    assert len(state["pootle_staged"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_remove(localfs, localfs_dummy_finder_empty):
    plugin = localfs
    plugin.resources.tracked.update(
        last_sync_hash=None,
        last_sync_revision=None,
        staged_for_removal=True)
    state = plugin.state()
    assert len(state["remove"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_pootle_staged_real(localfs_base, settings):
    from pytest_pootle.utils import add_store_fs

    plugin = localfs_base
    for store in plugin.resources.stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))
    state = plugin.state()
    assert len(state["pootle_staged"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_force_added(localfs, localfs_dummy_finder):
    from pootle_store.models import POOTLE_WINS

    plugin = localfs
    for store_fs in plugin.resources.tracked:
        store_fs.last_sync_revision = store_fs.last_sync_revision - 1
        store_fs.resolve_conflict = POOTLE_WINS
        store_fs.save()
    state = plugin.state()
    assert len(state["pootle_ahead"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin


@pytest.fixture
def localfs_force_fetched(localfs, localfs_dummy_finder):
    from pootle_store.models import FILE_WINS

    plugin = localfs
    for store_fs in plugin.resources.tracked:
        store_fs.last_sync_revision = store_fs.last_sync_revision - 1
        store_fs.resolve_conflict = FILE_WINS
        store_fs.save()
    state = plugin.state()
    assert len(state["fs_ahead"]) == plugin.resources.tracked.count()
    assert len([x for x in state]) == 1
    return plugin

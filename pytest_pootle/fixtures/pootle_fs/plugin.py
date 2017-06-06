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


RESPONSE_MAP = {
    "conflict": dict(
        rm_force=("staged_for_removal", "remove"),
        resolve_overwrite=("staged_for_overwrite_fs", "fs_staged"),
        resolve_pootle_overwrite=("staged_for_overwrite_pootle", "pootle_staged"),
        resolve_pootle=("staged_for_merge_pootle", "merge_pootle_wins"),
        resolve=("staged_for_merge_fs", "merge_fs_wins")),
    "conflict_untracked": dict(
        rm_force=("staged_for_removal", "remove"),
        resolve_pootle_overwrite=("staged_for_overwrite_pootle", "pootle_staged"),
        resolve_overwrite=("staged_for_overwrite_fs", "fs_staged"),
        resolve_pootle=("staged_for_merge_pootle", "merge_pootle_wins"),
        resolve=("staged_for_merge_fs", "merge_fs_wins")),
    "fs_ahead": dict(
        sync=("pulled_to_pootle", None)),
    "fs_removed": dict(
        add_force=("readded_from_pootle", "pootle_staged"),
        rm=("staged_for_removal", "remove"),
        rm_force=("staged_for_removal", "remove")),
    "fs_staged": dict(
        sync=("pulled_to_pootle", None)),
    "fs_untracked": dict(
        add=("added_from_fs", "fs_staged"),
        add_force=("added_from_fs", "fs_staged"),
        rm_force=("staged_for_removal", "remove")),
    "merge_fs_wins": dict(
        sync=("merged_from_fs", None)),
    "merge_pootle_wins": dict(
        sync=("merged_from_pootle", None)),
    "pootle_ahead": dict(
        sync=("pushed_to_fs", None)),
    "pootle_removed": dict(
        add_force=("readded_from_fs", "fs_staged"),
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
        request.getfixturevalue(
            "localfs_%s" % localfs_env_names))


@pytest.fixture(params=["force_added"])
def localfs_staged_envs(request):
    return (
        request.param,
        request.getfixturevalue(
            "localfs_%s" % request.param))


@pytest.fixture
def localfs_env(project_fs, no_complex_po_, revision):
    return project_fs


@pytest.fixture
def localfs_base(localfs_env):
    localfs_env.resources.tracked.delete()
    shutil.rmtree(localfs_env.fs_url)
    os.makedirs(
        os.path.join(
            localfs_env.fs_url,
            localfs_env.project.code))
    return localfs_env


@pytest.fixture
def localfs_dummy_finder(dummy_fs_finder, localfs_env):
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
    def get_fs_finder_(**kwargs_):
        return DummyFSFinder


@pytest.fixture
def localfs_dummy_finder_empty(dummy_fs_finder, localfs_env):
    from pootle.core.plugin import getter
    from pootle_fs.delegate import fs_finder
    from pootle_fs.finder import TranslationFileFinder

    plugin = localfs_env

    class DummyEmptyFSFinder(TranslationFileFinder):

        def find(self):
            return []

    @getter(fs_finder, sender=plugin.__class__, weak=False)
    def get_fs_finder_(**kwargs_):
        return DummyEmptyFSFinder


@pytest.fixture
def localfs_dummy_file(dummy_fs_files):
    from pootle.core.plugin import getter
    from pootle_fs.delegate import fs_file
    from pootle_fs.files import FSFile
    from pootle_fs.localfs import LocalFSPlugin

    class DummyFSFile(FSFile):

        _added = False
        _deleted = False
        _merged = False
        _pulled = False
        _pushed = False
        _resolved = False
        _removed = False
        _saved = False
        _synced = False
        _unstaged = False

        @property
        def latest_hash(self):
            return str(hash(self.pootle_path))

        def delete(self):
            self._deleted = True

        def on_sync(self, sync_hash, sync_revision, save=False):
            self._sync_hash = sync_hash
            self._sync_revision = sync_revision
            self._synced = True
            self._saved = save

        def pull(self, **kwargs):
            self._pulled = True
            self._pull_data = sorted(kwargs.items())

        def push(self):
            self._pushed = True

    @getter(fs_file, sender=LocalFSPlugin, weak=False)
    def get_fs_file_(**kwargs_):
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
def localfs_fs_untracked(no_complex_po_, localfs_base,
                         localfs_dummy_finder, localfs_dummy_file):
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
    from pootle_store.constants import SOURCE_WINS

    plugin = localfs

    stores = plugin.resources.stores
    plugin.resources.tracked.update(
        resolve_conflict=SOURCE_WINS,
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
def localfs_pootle_staged_real(localfs_base):
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

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from fnmatch import fnmatch

import pytest

from pytest_pootle.factories import ProjectDBFactory
from pytest_pootle.fixtures.pootle_fs.state import DummyPlugin
from pytest_pootle.utils import add_store_fs

from pootle_fs.models import StoreFS
from pootle_fs.state import FS_STATE, ProjectFSState
from pootle_store.models import FILE_WINS, POOTLE_WINS, Store


def _test_state_type(plugin, state, state_type, empty=False):
    assert not state.state_unchanged
    if not empty:
        assert state[state_type]
    else:
        assert not state[state_type]
    for k in state.states:
        if k != state_type:
            assert not state[k]
    for item in state[state_type]:
        assert isinstance(item, state.item_state_class)
        assert item.fs_path == plugin.get_fs_path(item.pootle_path)
        if item.store_fs:
            assert item.pootle_path == item.store_fs.pootle_path
        elif item.store:
            assert item.pootle_path == item.store.pootle_path
        assert item.project is plugin.project
        assert item.plugin is plugin
    assert (
        sorted(state[state_type])
        == sorted(state[state_type], key=lambda x: x.pootle_path))
    if not empty:
        assert state[state_type][0] > 0


@pytest.mark.django_db
def test_fs_state_instance(settings, english):
    settings.POOTLE_FS_PATH = "/tmp/foo/"
    project = ProjectDBFactory(source_language=english)
    plugin = DummyPlugin(project)
    state = ProjectFSState(plugin)
    assert state.project == project
    assert state.states == FS_STATE.keys()
    assert (
        str(state)
        == ("<ProjectFSState(<DummyPlugin(%s)>): Nothing to report>"
            % project.fullname))


@pytest.mark.django_db
def test_fs_state_fs_untracked(fs_path_qs, project0_dummy_plugin_del_stores):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_del_stores
    StoreFS.objects.filter(project=plugin.project).delete()
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    found = [
        dict(pootle_path=pp, fs_path=fp)
        for pp, fp
        in plugin.find_translations(pootle_path=pootle_path, fs_path=fs_path)]
    assert found == list(state.state_fs_untracked)
    assert len(state["fs_untracked"]) == len(found)
    _test_state_type(plugin, state, "fs_untracked", not found)


@pytest.mark.django_db
def test_fs_state_pootle_untracked(fs_path_qs, project0_dummy_plugin_no_files):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_no_files
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores = state.resources.store_filter.filtered(
        Store.objects.filter(translation_project__project=plugin.project))
    if fs_path:
        stores = [
            store for store
            in stores
            if fnmatch(plugin.get_fs_path(store.pootle_path), fs_path)]
    else:
        stores = list(stores)
    assert len(stores) == len(list(state.state_pootle_untracked))
    assert len(state["pootle_untracked"]) == len(stores)
    if len(stores):
        assert state["pootle_untracked"]
    assert len(state["pootle_untracked"]) == len(stores)
    _test_state_type(plugin, state, "pootle_untracked", not stores)


@pytest.mark.django_db
def test_fs_state_fs_removed(fs_path_qs, project0_dummy_plugin_no_files):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_no_files
    stores = Store.objects.filter(translation_project__project=plugin.project)
    for store in stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores = state.resources.store_filter.filtered(stores)
    if fs_path:
        stores = [
            store for store
            in stores
            if fnmatch(plugin.get_fs_path(store.pootle_path), fs_path)]
    else:
        stores = list(stores)
    assert len(stores) == len(list(state.state_fs_removed))
    assert len(state["fs_removed"]) == len(stores)
    if len(stores):
        assert state["fs_removed"]
    assert len(state["fs_removed"]) == len(stores)
    _test_state_type(plugin, state, "fs_removed", not stores)


@pytest.mark.django_db
def test_fs_state_pootle_ahead(fs_path_queries):
    plugin, (qfilter, pootle_path, fs_path) = fs_path_queries
    stores = Store.objects.filter(translation_project__project=plugin.project)
    for store in stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
        unit = store.units[0]
        unit.target = "%sFOO!" % store.name
        unit.save()
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores = state.resources.store_filter.filtered(stores)
    if fs_path:
        stores = [
            store for store
            in stores
            if fnmatch(plugin.get_fs_path(store.pootle_path), fs_path)]
    else:
        stores = list(stores)
    assert len(stores) == len(list(state.state_pootle_ahead))
    if len(stores):
        assert state["pootle_ahead"]
    assert len(state["pootle_ahead"]) == len(stores)
    _test_state_type(plugin, state, "pootle_ahead", not stores)


@pytest.mark.django_db
def test_fs_state_fs_staged(fs_path_qs, project0_dummy_plugin_del_stores):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_del_stores
    stores_fs = StoreFS.objects.filter(project=plugin.project)
    for storefs in stores_fs:
        storefs.last_sync_hash = None
        storefs.last_sync_revision = None
        storefs.resolve_conflict = FILE_WINS
        storefs.save()
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    assert len(list(state.state_fs_staged)) == stores_fs.count()
    for store_fs in state.state_fs_staged:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["fs_staged"]) == stores_fs.count()
    _test_state_type(plugin, state, "fs_staged", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_fs_staged_store_removed(fs_path_qs,
                                          project0_dummy_plugin_del_stores):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_del_stores
    stores_fs = StoreFS.objects.filter(project=plugin.project)
    for storefs in stores_fs:
        storefs.resolve_conflict = FILE_WINS
        storefs.save()
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    assert len(list(state.state_fs_staged)) == stores_fs.count()
    assert len(state["fs_staged"]) == stores_fs.count()
    for store_fs in state.state_fs_staged:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["fs_staged"]) == stores_fs.count()
    _test_state_type(plugin, state, "fs_staged", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_pootle_staged(fs_path_qs, project0_dummy_plugin_no_files):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_no_files
    stores = Store.objects.filter(
        translation_project__project=plugin.project)
    for store in stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    assert len(list(state.state_pootle_staged)) == stores_fs.count()
    assert len(state["pootle_staged"]) == stores_fs.count()
    for store_fs in state.state_pootle_staged:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["pootle_staged"]) == stores_fs.count()
    _test_state_type(plugin, state, "pootle_staged", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_pootle_staged_no_file(fs_path_qs, project0_dummy_plugin_no_files):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_no_files
    stores = Store.objects.filter(
        translation_project__project=plugin.project)
    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
        store_fs.resolve_conflict = POOTLE_WINS
        store_fs.save()
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    assert len(list(state.state_pootle_staged)) == stores_fs.count()
    for store_fs in state.state_pootle_staged:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["pootle_staged"]) == stores_fs.count()
    _test_state_type(plugin, state, "pootle_staged", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_both_removed(fs_path_qs, project0_dummy_plugin_no_files):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_no_files
    stores = Store.objects.filter(
        translation_project__project=plugin.project)
    for store in stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
    stores.delete()
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    assert len(list(state.state_both_removed)) == stores_fs.count()
    for store_fs in state.state_both_removed:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["both_removed"]) == stores_fs.count()
    _test_state_type(plugin, state, "both_removed", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_pootle_removed(fs_path_qs, project0_dummy_plugin_del_stores):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_del_stores
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    assert len(list(state.state_pootle_removed)) == stores_fs.count()
    for store_fs in state.state_pootle_removed:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["pootle_removed"]) == stores_fs.count()
    _test_state_type(plugin, state, "pootle_removed", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_conflict_untracked(fs_path_queries):
    plugin, (qfilter, pootle_path, fs_path) = fs_path_queries
    stores = Store.objects.filter(
        translation_project__project=plugin.project)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores = state.resources.store_filter.filtered(stores)
    if fs_path:
        stores = [
            store for store
            in stores
            if fnmatch(plugin.get_fs_path(store.pootle_path), fs_path)]
    else:
        stores = list(stores)
    assert len(list(state.state_conflict_untracked)) == len(stores)
    for result in state.state_conflict_untracked:
        assert result["store"] in stores
        if fs_path:
            assert fnmatch(result["fs_path"], fs_path)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    assert len(state["conflict_untracked"]) == len(stores)
    _test_state_type(plugin, state, "conflict_untracked", not stores)


@pytest.mark.django_db
def test_fs_state_merge_fs_synced(fs_path_queries):
    plugin, (qfilter, pootle_path, fs_path) = fs_path_queries
    stores = Store.objects.filter(
        translation_project__project=plugin.project)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores = state.resources.store_filter.filtered(stores)
    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
        store_fs.staged_for_merge = True
        store_fs.resolve_conflict = FILE_WINS
        store_fs.save()
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    assert len(list(state.state_merge_fs_wins)) == stores_fs.count()
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    for store_fs in state.state_merge_fs_wins:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["merge_fs_wins"]) == stores_fs.count()
    _test_state_type(plugin, state, "merge_fs_wins", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_merge_fs_unsynced(fs_path_queries):
    plugin, (qfilter, pootle_path, fs_path) = fs_path_queries
    stores = Store.objects.filter(
        translation_project__project=plugin.project)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores = state.resources.store_filter.filtered(stores)
    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))
        store_fs.staged_for_merge = True
        store_fs.resolve_conflict = FILE_WINS
        store_fs.save()
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    assert len(list(state.state_merge_fs_wins)) == stores_fs.count()
    for store_fs in state.state_merge_fs_wins:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["merge_fs_wins"]) == stores_fs.count()
    _test_state_type(plugin, state, "merge_fs_wins", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_merge_pootle_synced(fs_path_queries):
    plugin, (qfilter, pootle_path, fs_path) = fs_path_queries
    stores = Store.objects.filter(
        translation_project__project=plugin.project)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores = state.resources.store_filter.filtered(stores)
    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
        store_fs.staged_for_merge = True
        store_fs.resolve_conflict = POOTLE_WINS
        store_fs.save()
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    assert len(list(state.state_merge_pootle_wins)) == stores_fs.count()
    for store_fs in state.state_merge_pootle_wins:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["merge_pootle_wins"]) == stores_fs.count()
    _test_state_type(plugin, state, "merge_pootle_wins", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_merge_pootle_unsynced(fs_path_queries):
    plugin, (qfilter, pootle_path, fs_path) = fs_path_queries
    stores = Store.objects.filter(
        translation_project__project=plugin.project)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores = state.resources.store_filter.filtered(stores)
    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))
        store_fs.staged_for_merge = True
        store_fs.resolve_conflict = POOTLE_WINS
        store_fs.save()
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    assert len(list(state.state_merge_pootle_wins)) == stores_fs.count()
    for store_fs in state.state_merge_pootle_wins:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["merge_pootle_wins"]) == stores_fs.count()
    _test_state_type(plugin, state, "merge_pootle_wins", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_remove(fs_path_queries):
    plugin, (qfilter, pootle_path, fs_path) = fs_path_queries
    stores = Store.objects.filter(
        translation_project__project=plugin.project)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores = state.resources.store_filter.filtered(stores)
    for store in stores:
        store_fs = add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path))
        store_fs.staged_for_removal = True
        store_fs.save()
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    assert len(list(state.state_remove)) == stores_fs.count()
    for store_fs in state.state_remove:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["remove"]) == stores_fs.count()
    _test_state_type(plugin, state, "remove", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_conflict(fs_path_qs, project0_dummy_plugin_fs_changed):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_fs_changed
    stores = Store.objects.filter(translation_project__project=plugin.project)
    for store in stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
        unit = store.units[0]
        unit.target = "%sFOO!" % store.name
        unit.save()
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    assert len(list(state.state_conflict)) == stores_fs.count()
    for store_fs in state.state_conflict:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["conflict"]) == stores_fs.count()
    _test_state_type(plugin, state, "conflict", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_fs_ahead(fs_path_qs, project0_dummy_plugin_fs_changed):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_fs_changed
    stores = Store.objects.filter(translation_project__project=plugin.project)
    for store in stores:
        add_store_fs(
            store=store,
            fs_path=plugin.get_fs_path(store.pootle_path),
            synced=True)
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    assert len(list(state.state_fs_ahead)) == stores_fs.count()
    for store_fs in state.state_fs_ahead:
        assert store_fs["store_fs"] in stores_fs
    assert len(state["fs_ahead"]) == stores_fs.count()
    _test_state_type(plugin, state, "fs_ahead", not stores_fs.count())


@pytest.mark.django_db
def test_fs_state_pootle_removed_obsolete(fs_path_qs,
                                          project0_dummy_plugin_obs_stores):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = project0_dummy_plugin_obs_stores
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    stores_fs = state.resources.storefs_filter.filtered(state.resources.tracked)
    assert len(list(state.state_pootle_removed)) == stores_fs.count()
    for store_fs in state.state_pootle_removed:
        assert store_fs["store_fs"] in stores_fs

    assert len(state["pootle_removed"]) == stores_fs.count()
    _test_state_type(plugin, state, "pootle_removed", not stores_fs.count())

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import sys
from copy import copy

import pytest

from pytest_pootle.factories import ProjectDBFactory
from pytest_pootle.fixtures.pootle_fs.state import DummyPlugin

from pootle_fs.models import StoreFS
from pootle_fs.resources import FSProjectStateResources
from pootle_fs.state import FS_STATE, ProjectFSState
from pootle_store.constants import POOTLE_WINS, SOURCE_WINS


def _test_state(plugin, pootle_path, fs_path, state_type, paths=None,
                exclude_templates=False):
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    if paths is None:
        paths = state.resources.storefs_filter.filtered(
            state.resources.tracked)
        if exclude_templates:
            paths = paths.exclude(
                store__translation_project__language__code="templates")
        paths = list(paths.values_list("pootle_path", "path"))
    state_paths = []
    for item in getattr(state, "state_%s" % state_type):
        if item.get("pootle_path"):
            pootle_path = item["pootle_path"]
        else:
            pootle_path = item["store"].pootle_path
        fs_path = item["fs_path"]
        state_paths.append((pootle_path, fs_path))
    result_state_paths = []
    for item in sorted(reversed(state[state_type])):
        assert isinstance(item, state.item_state_class)
        assert item > None
        assert item.project == plugin.project
        assert item.store == item.kwargs.get("store")
        result_state_paths.append((item.pootle_path, item.fs_path))
    assert sorted(state_paths) == result_state_paths == sorted(paths)


@pytest.mark.django_db
def test_fs_state_instance(settings, english):
    settings.POOTLE_FS_WORKING_PATH = "/tmp/foo/"
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
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_fs_untracked(fs_path_qs, dummyfs_plugin_del_stores):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_del_stores
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    paths = list(
        state.resources.storefs_filter.filtered(
            state.resources.tracked).values_list("pootle_path", "path"))
    plugin.resources.tracked.delete()
    _test_state(plugin, pootle_path, fs_path, "fs_untracked", paths)


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_pootle_untracked(fs_path_qs, dummyfs_plugin_no_files):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_no_files
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    paths = list(
        state.resources.storefs_filter.filtered(
            state.resources.tracked).values_list("pootle_path", "path"))
    plugin.resources.tracked.delete()
    _test_state(plugin, pootle_path, fs_path, "pootle_untracked", paths)


@pytest.mark.django_db
def test_fs_state_fs_removed(fs_path_qs, dummyfs_plugin_no_files):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_no_files
    _test_state(plugin, pootle_path, fs_path, "fs_removed")


@pytest.mark.django_db
def test_fs_state_pootle_ahead(fs_path_qs, dummyfs_plugin_fs_unchanged):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_fs_unchanged
    for sfs in plugin.resources.tracked:
        sfs.last_sync_hash = sfs.file.latest_hash
        sfs.last_sync_revision = (
            sfs.store.data.max_unit_revision - 1
            if sfs.store.data.max_unit_revision
            else 0)
        sfs.save()
    _test_state(
        plugin,
        pootle_path,
        fs_path,
        "pootle_ahead",
        exclude_templates=True)


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_fs_staged(fs_path_qs, dummyfs_plugin_del_stores):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_del_stores
    plugin.resources.tracked.update(
        last_sync_hash=None,
        last_sync_revision=None,
        resolve_conflict=SOURCE_WINS)
    _test_state(plugin, pootle_path, fs_path, "fs_staged")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_fs_staged_store_removed(fs_path_qs,
                                          dummyfs_plugin_del_stores):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_del_stores
    plugin.resources.tracked.update(resolve_conflict=SOURCE_WINS)
    _test_state(plugin, pootle_path, fs_path, "fs_staged")


@pytest.mark.django_db
def test_fs_state_pootle_staged(fs_path_qs, dummyfs_plugin_no_files):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_no_files
    plugin.resources.tracked.update(last_sync_hash=None, last_sync_revision=None)
    _test_state(plugin, pootle_path, fs_path, "pootle_staged")


@pytest.mark.django_db
def test_fs_state_pootle_staged_no_file(fs_path_qs, dummyfs_plugin_no_files):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_no_files
    plugin.resources.tracked.update(resolve_conflict=POOTLE_WINS)
    _test_state(plugin, pootle_path, fs_path, "pootle_staged")


@pytest.mark.django_db
def test_fs_state_both_removed(fs_path_qs, dummyfs_plugin_no_files):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_no_files
    plugin.resources.stores.delete()
    _test_state(plugin, pootle_path, fs_path, "both_removed")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_pootle_removed(dummyfs_plugin_del_stores, fs_path_qs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_del_stores
    _test_state(plugin, pootle_path, fs_path, "pootle_removed")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_conflict_untracked(fs_path_qs, no_complex_po_, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    state = ProjectFSState(plugin, pootle_path=pootle_path, fs_path=fs_path)
    paths = list(
        state.resources.storefs_filter.filtered(
            state.resources.tracked).values_list("pootle_path", "path"))
    plugin.resources.tracked.delete()
    _test_state(plugin, pootle_path, fs_path, "conflict_untracked", paths)


@pytest.mark.django_db
def test_fs_state_merge_fs_synced(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    plugin.resources.tracked.update(
        resolve_conflict=SOURCE_WINS, staged_for_merge=True)
    _test_state(plugin, pootle_path, fs_path, "merge_fs_wins")


@pytest.mark.django_db
def test_fs_state_merge_fs_unsynced(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    plugin.resources.tracked.update(
        resolve_conflict=SOURCE_WINS, staged_for_merge=True,
        last_sync_hash=None, last_sync_revision=None)
    _test_state(plugin, pootle_path, fs_path, "merge_fs_wins")


@pytest.mark.django_db
def test_fs_state_merge_pootle_synced(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    plugin.resources.tracked.update(
        resolve_conflict=POOTLE_WINS, staged_for_merge=True)
    _test_state(plugin, pootle_path, fs_path, "merge_pootle_wins")


@pytest.mark.django_db
def test_fs_state_merge_pootle_unsynced(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    plugin.resources.tracked.update(
        resolve_conflict=POOTLE_WINS, staged_for_merge=True,
        last_sync_hash=None, last_sync_revision=None)
    _test_state(plugin, pootle_path, fs_path, "merge_pootle_wins")


@pytest.mark.django_db
def test_fs_state_remove(fs_path_qs, dummyfs):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs
    plugin.resources.tracked.update(staged_for_removal=True)
    _test_state(plugin, pootle_path, fs_path, "remove")


@pytest.mark.django_db
def test_fs_state_conflict(fs_path_qs, dummyfs_plugin_fs_changed):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_fs_changed
    for store_fs in plugin.resources.tracked:
        store_fs.last_sync_revision = store_fs.last_sync_revision - 1
        store_fs.save()
    _test_state(plugin, pootle_path, fs_path, "conflict")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_fs_ahead(fs_path_qs, dummyfs_plugin_fs_changed):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_fs_changed
    _test_state(plugin, pootle_path, fs_path, "fs_ahead")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_pootle_removed_obsolete(fs_path_qs,
                                          dummyfs_plugin_obs_stores):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = dummyfs_plugin_obs_stores
    _test_state(plugin, pootle_path, fs_path, "pootle_removed")


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_filtered(state_filters, dummyfs_plugin_no_files, tp0):
    plugin = dummyfs_plugin_no_files
    state = ProjectFSState(plugin)
    current_state = {
        k: copy(v)
        for k, v
        in state.__state__.items()}
    filtered_state = state.filter(**state_filters)
    pootle_paths = state_filters["pootle_paths"]
    fs_paths = state_filters["fs_paths"]
    states = state_filters["states"]
    # original is unchanged
    assert state.__state__ == current_state
    for name, items in state.__state__.items():
        if states and name not in states:
            assert filtered_state[name] == []
            continue
        assert (
            [(item.fs_path, item.pootle_path)
             for item in items
             if (not pootle_paths
                 or item.pootle_path in pootle_paths)
             and (not fs_paths
                  or item.fs_path in fs_paths)]
            == [(x.fs_path, x.pootle_path) for x in filtered_state[name]])


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_fs_state_fs_unchanged(fs_path_qs, no_complex_po_, dummyfs):
    plugin = dummyfs
    (qfilter, pootle_path, fs_path) = fs_path_qs

    class UnchangedStateResources(FSProjectStateResources):

        @property
        def file_hashes(self):
            hashes = {}
            for pootle_path, path in self.found_file_matches:
                hashes[pootle_path] = self.tracked.get(
                    pootle_path=pootle_path).last_sync_hash
            return hashes

    class UnchangedFSState(ProjectFSState):

        @property
        def resources(self):
            return UnchangedStateResources(
                self.context,
                pootle_path=self.pootle_path,
                fs_path=self.fs_path)

    state = UnchangedFSState(plugin, fs_path=fs_path, pootle_path=pootle_path)
    expected = (
        plugin.resources.tracked.filter(qfilter)
        if qfilter
        else plugin.resources.tracked)
    if qfilter is False:
        expected = plugin.resources.tracked.none()
    stores_fs = [x["store_fs"] for x in state.state_unchanged]
    assert (
        stores_fs
        == list(
            expected.order_by("pootle_path").values_list("id", flat=True)))
    StoreFS.objects.filter(pk__in=stores_fs).update(staged_for_removal=True)
    state = UnchangedFSState(plugin, fs_path=fs_path, pootle_path=pootle_path)
    assert len(list(state.state_unchanged)) == 0

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from pytest_pootle.fs.utils import filtered_fs_matches, filtered_fs_stores

from pootle.core.response import Response
from pootle.core.state import State
from pootle_fs.matcher import FSPathMatcher
from pootle_fs.plugin import Plugin
from pootle_fs.utils import FSPlugin
from pootle_project.models import Project


def _test_dummy_response(responses, **kwargs):
    stores = kwargs.pop("stores", None)
    if stores:
        assert len(responses) == len(stores)
    stores_fs = kwargs.pop("stores_fs", None)
    if stores_fs:
        assert len(responses) == len(stores_fs)
    paths = kwargs.pop("paths", None)
    if paths:
        assert len(responses) == len(paths)
    expected_keys = [
        "_added", "_fetched", "_pulled",
        "_synced", "_pushed", "_merged",
        "_removed", "_unstaged"]
    for response in responses:
        if stores:
            assert response.store_fs.store in stores
        if stores_fs:
            assert response.store_fs in stores_fs
        if paths:
            assert (response.pootle_path, response.fs_path) in paths
        for k in expected_keys:
            assert getattr(response.store_fs.file, k) == kwargs.get(k, False)
        for k in kwargs:
            if k not in expected_keys:
                assert getattr(response.store_fs.file, k) == kwargs[k]


@pytest.mark.django_db
def test_plugin_instance_bad_args(project_fs_empty):
    fs_plugin = project_fs_empty.plugin

    with pytest.raises(TypeError):
        fs_plugin.__class__()

    with pytest.raises(TypeError):
        fs_plugin.__class__("FOO")


@pytest.mark.django_db
def test_plugin_pull(project_fs_empty):
    assert project_fs_empty.is_cloned is False
    project_fs_empty.pull()
    assert project_fs_empty.is_cloned is True
    project_fs_empty.clear_repo()
    assert project_fs_empty.is_cloned is False


@pytest.mark.django_db
def test_plugin_instance(project_fs_empty):
    project_fs = project_fs_empty
    assert project_fs.project == project_fs.plugin.project
    assert project_fs.project.local_fs_path.endswith(project_fs.project.code)
    assert project_fs.is_cloned is False
    assert project_fs.resources.stores.exists() is False
    assert project_fs.resources.tracked.exists() is False
    # any instance of the same plugin is equal
    new_plugin = FSPlugin(project_fs.project)
    assert project_fs == new_plugin
    assert project_fs is not new_plugin
    # but the plugin doesnt equate to a cabbage 8)
    assert not project_fs == "a cabbage"


@pytest.mark.django_db
def test_plugin_pootle_user(project_fs_empty, member):
    project = project_fs_empty.project
    assert "pootle_fs.pootle_user" not in project.config
    assert project_fs_empty.pootle_user is None
    project.config["pootle_fs.pootle_user"] = member.username
    assert project_fs_empty.pootle_user is None
    project_fs_empty.reload()
    assert project_fs_empty.pootle_user == member


@pytest.mark.django_db
def test_plugin_pootle_user_bad(project_fs_empty, member):
    project = project_fs_empty.project
    project.config["pootle_fs.pootle_user"] = "USER_DOES_NOT_EXIST"
    project_fs_empty.reload()
    assert project_fs_empty.pootle_user is None


###########
# ADD TESTS
###########

@pytest.mark.django_db
def test_fs_plugin_add(fs_path_qs, localfs_pootle_untracked):
    """tests `add` against `pootle_untracked`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_pootle_untracked
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["pootle_untracked"])
    _test_dummy_response(
        plugin.add(
            pootle_path=pootle_path,
            fs_path=fs_path)["added_from_pootle"],
        stores=stores,
        _added=True)


@pytest.mark.django_db
def test_fs_plugin_add_fs_removed(fs_path_qs, localfs_fs_removed):
    """tests `add` against `fs_removed`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_fs_removed
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["fs_removed"])
    response = plugin.add(pootle_path=pootle_path, fs_path=fs_path)
    assert len(response["added_from_pootle"]) == 0
    _test_dummy_response(
        plugin.add(
            pootle_path=pootle_path,
            fs_path=fs_path,
            force=True)["added_from_pootle"],
        stores=stores,
        _added=True)


@pytest.mark.django_db
def test_fs_plugin_add_conflict(fs_path_qs, localfs_conflict):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_conflict
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["conflict"])
    response = plugin.add(pootle_path=pootle_path, fs_path=fs_path)
    assert len(response["added_from_pootle"]) == 0
    response = plugin.add(pootle_path=pootle_path, fs_path=fs_path, force=True)
    assert len(response["added_from_pootle"]) == len(stores)
    _test_dummy_response(
        plugin.add(
            pootle_path=pootle_path,
            fs_path=fs_path,
            force=True)["added_from_pootle"],
        stores=stores,
        _added=True)


@pytest.mark.django_db
def test_fs_plugin_add_conflict_untracked(fs_path_qs,
                                          localfs_conflict_untracked):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_conflict_untracked
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    response = plugin.add(pootle_path=pootle_path, fs_path=fs_path)
    assert len(response["added_from_pootle"]) == 0
    _test_dummy_response(
        plugin.add(
            pootle_path=pootle_path,
            fs_path=fs_path,
            force=True)["added_from_pootle"],
        stores=stores,
        _added=True)


#############
# FETCH TESTS
#############

@pytest.mark.django_db
def test_fs_plugin_fetch(fs_path_qs, localfs_fs_untracked):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_fs_untracked
    state, matches = filtered_fs_matches(plugin, fs_path, pootle_path)
    assert len(matches) == len(state["fs_untracked"])
    _test_dummy_response(
        plugin.fetch(
            pootle_path=pootle_path,
            fs_path=fs_path)["fetched_from_fs"],
        _fetched=True,
        paths=matches)


@pytest.mark.django_db
def test_fs_plugin_fetch_conflict(fs_path_qs, localfs_conflict):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_conflict
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["conflict"])
    response = plugin.fetch(pootle_path=pootle_path, fs_path=fs_path)
    assert len(response["fetched_from_fs"]) == 0
    _test_dummy_response(
        plugin.fetch(
            pootle_path=pootle_path,
            fs_path=fs_path,
            force=True)["fetched_from_fs"],
        stores=stores,
        _fetched=True)


@pytest.mark.django_db
def test_fs_plugin_fetch_pootle_removed(fs_path_qs,
                                        localfs_pootle_removed):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_pootle_removed
    state = plugin.state(fs_path=fs_path, pootle_path=pootle_path)
    stores_fs = state.resources.storefs_filter.filtered(
        plugin.project.store_fs.all())
    assert len(stores_fs) == len(state["pootle_removed"])
    response = plugin.fetch(pootle_path=pootle_path, fs_path=fs_path)
    assert len(response["fetched_from_fs"]) == 0
    _test_dummy_response(
        plugin.fetch(
            pootle_path=pootle_path,
            fs_path=fs_path,
            force=True)["fetched_from_fs"],
        stores_fs=stores_fs,
        _fetched=True)


@pytest.mark.django_db
def test_fs_plugin_fetch_conflict_untracked(fs_path_qs,
                                            localfs_conflict_untracked):
    """tests `fetch` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_conflict_untracked
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["conflict_untracked"])
    response = plugin.fetch(pootle_path=pootle_path, fs_path=fs_path)
    assert len(response["fetched_from_fs"]) == 0
    _test_dummy_response(
        plugin.fetch(
            pootle_path=pootle_path,
            fs_path=fs_path,
            force=True)["fetched_from_fs"],
        stores=stores,
        _fetched=True)


#############
# MERGE TESTS
#############

@pytest.mark.django_db
def test_fs_plugin_merge_conflict_untr(fs_path_qs,
                                       localfs_conflict_untracked):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_conflict_untracked
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["conflict_untracked"])
    _test_dummy_response(
        plugin.merge(
            pootle_path=pootle_path,
            fs_path=fs_path)["staged_for_merge_fs"],
        stores=stores,
        _merged=True,
        _merge_fs=True)


@pytest.mark.django_db
def test_fs_plugin_merge_conflict_untr_pootle(fs_path_qs,
                                              localfs_conflict_untracked):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_conflict_untracked
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["conflict_untracked"])
    _test_dummy_response(
        plugin.merge(
            pootle_path=pootle_path,
            fs_path=fs_path,
            pootle_wins=True)["staged_for_merge_pootle"],
        stores=stores,
        _merged=True,
        _merge_pootle=True)


@pytest.mark.django_db
def test_fs_plugin_merge_conflict(fs_path_qs,
                                  localfs_conflict):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_conflict
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["conflict"])
    _test_dummy_response(
        plugin.merge(
            pootle_path=pootle_path,
            fs_path=fs_path)["staged_for_merge_fs"],
        stores=stores,
        _merged=True,
        _merge_fs=True)


@pytest.mark.django_db
def test_fs_plugin_merge_conflict_pootle(fs_path_qs,
                                         localfs_conflict):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_conflict
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["conflict"])
    _test_dummy_response(
        plugin.merge(
            pootle_path=pootle_path,
            fs_path=fs_path,
            pootle_wins=True)["staged_for_merge_pootle"],
        stores=stores,
        _merged=True,
        _merge_pootle=True)


##########
# RM TESTS
##########

@pytest.mark.django_db
def test_fs_plugin_rm_pootle_removed(fs_path_qs,
                                     localfs_pootle_removed):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_pootle_removed
    state = plugin.state(fs_path=fs_path, pootle_path=pootle_path)
    stores_fs = state.resources.storefs_filter.filtered(
        plugin.project.store_fs.all())
    assert len(stores_fs) == len(state["pootle_removed"])
    _test_dummy_response(
        plugin.rm(
            pootle_path=pootle_path,
            fs_path=fs_path)["staged_for_removal"],
        stores_fs=stores_fs,
        _removed=True)


@pytest.mark.django_db
def test_fs_plugin_rm_fs_removed(fs_path_qs,
                                 localfs_fs_removed):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_fs_removed
    state = plugin.state(fs_path=fs_path, pootle_path=pootle_path)
    stores_fs = state.resources.storefs_filter.filtered(
        plugin.project.store_fs.all())
    assert len(stores_fs) == len(state["fs_removed"])
    _test_dummy_response(
        plugin.rm(
            pootle_path=pootle_path,
            fs_path=fs_path)["staged_for_removal"],
        stores_fs=stores_fs,
        _removed=True)


@pytest.mark.django_db
def test_fs_plugin_rm_pootle_untracked(fs_path_qs,
                                       localfs_pootle_untracked):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_pootle_untracked
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["pootle_untracked"])
    response = plugin.rm(pootle_path=pootle_path, fs_path=fs_path)
    assert len(response["staged_for_removal"]) == 0
    _test_dummy_response(
        plugin.rm(
            pootle_path=pootle_path,
            fs_path=fs_path,
            force=True)["staged_for_removal"],
        stores=stores,
        _removed=True)


@pytest.mark.django_db
def test_fs_plugin_rm_fs_untracked(fs_path_qs,
                                   localfs_fs_untracked):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_fs_untracked
    state, matches = filtered_fs_matches(plugin, fs_path, pootle_path)
    assert len(matches) == len(state["fs_untracked"])
    response = plugin.rm(pootle_path=pootle_path, fs_path=fs_path)
    assert len(response["staged_for_removal"]) == 0
    _test_dummy_response(
        plugin.rm(
            pootle_path=pootle_path,
            fs_path=fs_path,
            force=True)["staged_for_removal"],
        _removed=True)


@pytest.mark.django_db
def test_fs_plugin_rm_conflict_untracked(fs_path_qs,
                                         localfs_conflict_untracked):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_conflict_untracked
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["conflict_untracked"])
    response = plugin.rm(pootle_path=pootle_path, fs_path=fs_path)
    assert len(response["staged_for_removal"]) == 0
    _test_dummy_response(
        plugin.rm(
            pootle_path=pootle_path,
            fs_path=fs_path,
            force=True)["staged_for_removal"],
        stores=stores,
        _removed=True)


###############
# UNSTAGE TESTS
###############

@pytest.mark.django_db
def test_fs_plugin_unstage_pootle_staged(fs_path_qs,
                                         localfs_pootle_staged):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_pootle_staged
    state = plugin.state(fs_path=fs_path, pootle_path=pootle_path)
    stores_fs = state.resources.storefs_filter.filtered(
        plugin.project.store_fs.all())
    assert len(stores_fs) == len(state["pootle_staged"])
    _test_dummy_response(
        plugin.unstage(
            pootle_path=pootle_path,
            fs_path=fs_path)["unstaged"],
        stores_fs=stores_fs,
        _unstaged=True)


@pytest.mark.django_db
def test_fs_plugin_unstage_fs_staged(fs_path_qs, localfs_fs_staged):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_fs_staged
    state = plugin.state(fs_path=fs_path, pootle_path=pootle_path)
    stores_fs = state.resources.storefs_filter.filtered(
        plugin.project.store_fs.all())
    assert len(stores_fs) == len(state["fs_staged"])
    _test_dummy_response(
        plugin.unstage(
            pootle_path=pootle_path,
            fs_path=fs_path)["unstaged"],
        stores_fs=stores_fs,
        _unstaged=True)


@pytest.mark.django_db
def test_fs_plugin_unstage_merge_fs(fs_path_qs,
                                    localfs_merge_fs_wins):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_merge_fs_wins
    state = plugin.state(fs_path=fs_path, pootle_path=pootle_path)
    stores_fs = state.resources.storefs_filter.filtered(
        plugin.project.store_fs.all())
    assert len(stores_fs) == len(state["merge_fs_wins"])
    _test_dummy_response(
        plugin.unstage(
            pootle_path=pootle_path,
            fs_path=fs_path)["unstaged"],
        stores_fs=stores_fs,
        _unstaged=True)


@pytest.mark.django_db
def test_fs_plugin_unstage_merge_pootle(fs_path_qs,
                                        localfs_merge_pootle_wins):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_merge_pootle_wins
    state = plugin.state(fs_path=fs_path, pootle_path=pootle_path)
    stores_fs = state.resources.storefs_filter.filtered(
        plugin.project.store_fs.all())
    assert len(stores_fs) == len(state["merge_pootle_wins"])
    _test_dummy_response(
        plugin.unstage(
            pootle_path=pootle_path,
            fs_path=fs_path)["unstaged"],
        stores_fs=stores_fs,
        _unstaged=True)


@pytest.mark.django_db
def test_fs_plugin_unstage_force_added(fs_path_qs,
                                       localfs_force_added):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_force_added
    state = plugin.state(fs_path=fs_path, pootle_path=pootle_path)
    stores_fs = state.resources.storefs_filter.filtered(
        plugin.project.store_fs.all())
    assert len(stores_fs) == len(state["pootle_ahead"])
    _test_dummy_response(
        plugin.unstage(
            pootle_path=pootle_path,
            fs_path=fs_path)["unstaged"],
        stores_fs=stores_fs,
        _unstaged=True)


@pytest.mark.django_db
def test_fs_plugin_unstage_force_fetched(fs_path_qs,
                                         localfs_force_fetched):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_force_fetched

    state = plugin.state(fs_path=fs_path, pootle_path=pootle_path)
    stores_fs = state.resources.storefs_filter.filtered(
        plugin.project.store_fs.all())
    assert len(stores_fs) == len(state["fs_ahead"])
    _test_dummy_response(
        plugin.unstage(
            pootle_path=pootle_path,
            fs_path=fs_path)["unstaged"],
        stores_fs=stores_fs,
        _unstaged=True)


@pytest.mark.django_db
def test_fs_plugin_unstage_remove(fs_path_qs,
                                  localfs_remove):
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_remove
    state = plugin.state(fs_path=fs_path, pootle_path=pootle_path)
    stores_fs = state.resources.storefs_filter.filtered(
        plugin.project.store_fs.all())
    assert len(stores_fs) == len(state["remove"])
    _test_dummy_response(
        plugin.unstage(
            pootle_path=pootle_path,
            fs_path=fs_path)["unstaged"],
        stores_fs=stores_fs,
        _unstaged=True)


#######################
# MERGE RESOURCES TESTS
#######################

@pytest.mark.django_db
def test_fs_plugin_merge_pootle(fs_path_qs, localfs_merge_pootle_wins):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_merge_pootle_wins
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["merge_pootle_wins"])
    _test_dummy_response(
        plugin.sync_merge(
            pootle_path=pootle_path,
            fs_path=fs_path)["merged_from_pootle"],
        stores=stores,
        _pulled=True,
        _pushed=True,
        _pull_data=[("merge", True), ("pootle_wins", True), ("user", None)])


@pytest.mark.django_db
def test_fs_plugin_merge_fs(fs_path_qs, localfs_merge_fs_wins):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_merge_fs_wins
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["merge_fs_wins"])
    _test_dummy_response(
        plugin.sync_merge(
            pootle_path=pootle_path,
            fs_path=fs_path)["merged_from_fs"],
        stores=stores,
        _pulled=True,
        _pushed=True,
        _pull_data=[("merge", True), ("pootle_wins", False), ("user", None)])


######################
# PULL RESOURCES TESTS
######################

@pytest.mark.django_db
def test_fs_plugin_sync_pull_fs_ahead(fs_path_qs, localfs_fs_ahead):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_fs_ahead
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["fs_ahead"])
    _test_dummy_response(
        plugin.sync_pull(
            pootle_path=pootle_path, fs_path=fs_path)["pulled_to_pootle"],
        _pulled=True,
        stores=stores,
        _pull_data=[("user", None)])


@pytest.mark.django_db
def test_fs_plugin_sync_pull_fs_staged(fs_path_qs, localfs_fs_staged):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_fs_staged
    state, matches = filtered_fs_matches(plugin, fs_path, pootle_path)
    assert len(matches) == len(state["fs_staged"])
    _test_dummy_response(
        plugin.sync_pull(
            pootle_path=pootle_path, fs_path=fs_path)["pulled_to_pootle"],
        _pulled=True,
        paths=matches,
        _pull_data=[("user", None)])


####################
# RM RESOURCES TESTS
####################

@pytest.mark.django_db
def test_fs_plugin_sync_rm(fs_path_qs, localfs_remove):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_remove
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["remove"])
    _test_dummy_response(
        plugin.sync_rm(
            pootle_path=pootle_path, fs_path=fs_path)["removed"],
        stores=stores,
        _deleted=True)


######################
# PUSH RESOURCES TESTS
######################

@pytest.mark.django_db
def test_fs_plugin_sync_push_pootle_ahead(fs_path_qs, localfs_pootle_ahead):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_pootle_ahead
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["pootle_ahead"])
    _test_dummy_response(
        plugin.sync_push(
            pootle_path=pootle_path,
            fs_path=fs_path)["pushed_to_fs"],
        stores=stores,
        _pushed=True)


@pytest.mark.django_db
def test_fs_plugin_sync_push_pootle_staged(fs_path_qs, localfs_pootle_staged):
    """tests `add` against `conflict`"""
    (qfilter, pootle_path, fs_path) = fs_path_qs
    plugin = localfs_pootle_staged
    state, stores = filtered_fs_stores(plugin, fs_path, pootle_path)
    assert len(stores) == len(state["pootle_staged"])
    _test_dummy_response(
        plugin.sync_push(
            pootle_path=pootle_path,
            fs_path=fs_path)["pushed_to_fs"],
        stores=stores,
        _pushed=True)


@pytest.mark.django_db
def test_fs_plugin_sync_all():

    class SyncPlugin(Plugin):

        sync_order = []

        def push(self, response):
            self._push_response = response
            self.sync_order.append("plugin_push")
            return response

        def sync_merge(self, state, response, fs_path=None, pootle_path=None):
            self._merged = (state, response, fs_path, pootle_path)
            self.sync_order.append("merge")

        def sync_pull(self, state, response, fs_path=None, pootle_path=None):
            self._pulled = (state, response, fs_path, pootle_path)
            self.sync_order.append("pull")

        def sync_push(self, state, response, fs_path=None, pootle_path=None):
            self._pushed = (state, response, fs_path, pootle_path)
            self.sync_order.append("push")

        def sync_rm(self, state, response, fs_path=None, pootle_path=None):
            self._rmed = (state, response, fs_path, pootle_path)
            self.sync_order.append("rm")

    project = Project.objects.get(code="project0")
    plugin = SyncPlugin(project)
    state = State("dummy")
    response = Response(state)
    plugin.sync(state, response, fs_path="FOO", pootle_path="BAR")
    for result in [plugin._merged, plugin._pushed, plugin._rmed, plugin._pulled]:
        assert result[0] is state
        assert result[1] is response
        assert result[2] == "FOO"
        assert result[3] == "BAR"
    assert plugin._push_response is response
    assert plugin.sync_order == ["rm", "merge", "pull", "push", "plugin_push"]


@pytest.mark.django_db
def test_fs_plugin_not_implemented():
    project = Project.objects.get(code="project0")
    plugin = Plugin(project)

    with pytest.raises(NotImplementedError):
        plugin.pull()

    with pytest.raises(NotImplementedError):
        plugin.push()


@pytest.mark.django_db
def test_fs_plugin_matcher(localfs):
    matcher = localfs.matcher
    assert isinstance(matcher, FSPathMatcher)
    assert matcher is localfs.matcher
    localfs.reload()
    assert matcher is not localfs.matcher


@pytest.mark.django_db
def test_fs_plugin_localfs_push(localfs_pootle_staged_real):
    plugin = localfs_pootle_staged_real
    response = plugin.sync()
    for response_item in response["pushed_to_fs"]:
        src_file = os.path.join(
            plugin.fs_url,
            response_item.store_fs.file.path.lstrip("/"))
        target_file = response_item.store_fs.file.file_path
        with open(src_file) as target:
            with open(target_file) as src:
                assert src.read() == target.read()


@pytest.mark.django_db
def test_fs_plugin_synced_fs_ahead(localfs_fs_ahead):
    plugin = localfs_fs_ahead
    response = plugin.sync()
    for response_item in response["pulled_to_pootle"]:
        assert response_item.fs_state.store_fs.file._synced


@pytest.mark.django_db
def test_fs_plugin_synced_pootle_ahead(localfs_pootle_ahead):
    plugin = localfs_pootle_ahead
    response = plugin.sync()
    for response_item in response["pushed_to_fs"]:
        assert response_item.fs_state.store_fs.file._synced


@pytest.mark.django_db
def test_fs_plugin_synced_merge_fs_wins(localfs_merge_fs_wins):
    plugin = localfs_merge_fs_wins
    response = plugin.sync()
    assert response["merged_from_fs"]
    for response_item in response["merged_from_fs"]:
        assert response_item.fs_state.store_fs.file._synced


@pytest.mark.django_db
def test_fs_plugin_synced_merge_pootle_wins(localfs_merge_pootle_wins):
    plugin = localfs_merge_pootle_wins
    response = plugin.sync()
    assert response["merged_from_pootle"]
    for response_item in response["merged_from_pootle"]:
        assert response_item.fs_state.store_fs.file._synced

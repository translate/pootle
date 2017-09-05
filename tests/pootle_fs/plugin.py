# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import sys

import pytest

from pootle.core.delegate import revision
from pootle.core.response import Response
from pootle.core.state import State
from pootle_app.models import Directory
from pootle_fs.apps import PootleFSConfig
from pootle_fs.exceptions import FSStateError
from pootle_fs.matcher import FSPathMatcher
from pootle_fs.models import StoreFS
from pootle_fs.plugin import Plugin
from pootle_fs.utils import FSPlugin
from pootle_project.models import Project
from pootle_store.constants import POOTLE_WINS, SOURCE_WINS


FS_CHANGE_KEYS = [
    "_added", "_pulled",
    "_synced", "_pushed",
    "_resolved", "_removed", "_unstaged"]


def _test_dummy_response(action, responses, **kwargs):
    stores = kwargs.pop("stores", None)
    if stores:
        assert len(responses) == len(stores)
    stores_fs = kwargs.pop("stores_fs", None)
    if stores_fs:
        assert len(responses) == len(stores_fs)
    for response in responses:
        if action.startswith("add"):
            if response.fs_state.state_type.endswith("_untracked"):
                store_fs = StoreFS.objects.get(
                    pootle_path=response.pootle_path,
                    path=response.fs_path)
            else:
                store_fs = response.store_fs
                store_fs.refresh_from_db()
            if response.fs_state.state_type == "fs_removed":
                assert store_fs.resolve_conflict == POOTLE_WINS
            elif response.fs_state.state_type == "pootle_removed":
                assert store_fs.resolve_conflict == SOURCE_WINS
            assert not store_fs.staged_for_merge
            continue
        if action.startswith("rm"):
            if response.fs_state.state_type.endswith("_untracked"):
                store_fs = StoreFS.objects.get(
                    pootle_path=response.pootle_path,
                    path=response.fs_path)
            else:
                store_fs = response.store_fs
                store_fs.refresh_from_db()
            assert store_fs.staged_for_removal
            continue
        remove_states = ["fs_staged", "pootle_staged", "remove"]
        if action.startswith("unstage"):
            if response.fs_state.state_type in remove_states:
                with pytest.raises(StoreFS.DoesNotExist):
                    response.store_fs.refresh_from_db()
                continue
            store_fs = response.store_fs
            store_fs.refresh_from_db()
            assert not store_fs.staged_for_merge
            assert not store_fs.resolve_conflict
            continue
        if stores:
            if response.store_fs:
                assert response.store_fs.store in stores
            else:
                assert stores.filter(
                    pootle_path=response.pootle_path).exists()
        if action.startswith("resolve"):
            if response.fs_state.state_type.endswith("_untracked"):
                store_fs = StoreFS.objects.get(
                    path=response.fs_state.fs_path,
                    pootle_path=response.fs_state.pootle_path)
            else:
                store_fs = response.store_fs
                store_fs.refresh_from_db()
            if "pootle" in action:
                assert store_fs.resolve_conflict == POOTLE_WINS
            if not action.endswith("overwrite"):
                assert store_fs.staged_for_merge is True
            continue
        check_store_fs = (
            stores_fs
            and not response.fs_state.state_type == "fs_untracked")
        if check_store_fs:
            assert response.store_fs in stores_fs


@pytest.mark.django_db
@pytest.mark.xfail(
    sys.platform == 'win32',
    reason="path mangling broken on windows")
def test_fs_plugin_unstage_response(capsys, no_complex_po_, localfs_envs):
    state_type, plugin = localfs_envs
    action = "unstage"
    original_state = plugin.state()
    plugin_response = getattr(plugin, action)(state=original_state)
    unstaging_states = [
        "fs_staged", "pootle_staged", "remove",
        "merge_fs_wins", "merge_pootle_wins"]
    if state_type in unstaging_states:
        assert plugin_response.made_changes is True
        _test_dummy_response(
            action, plugin_response["unstaged"], _unstaged=True)
    else:
        assert plugin_response.made_changes is False
        assert not plugin_response["unstaged"]


@pytest.mark.django_db
def test_fs_plugin_unstage_staged_response(capsys,
                                           no_complex_po_,
                                           localfs_staged_envs):
    state_type, plugin = localfs_staged_envs
    action = "unstage"
    original_state = plugin.state()
    plugin_response = getattr(plugin, action)(
        state=original_state)
    assert plugin_response.made_changes is True
    _test_dummy_response(
        action, plugin_response["unstaged"], _unstaged=True)


@pytest.mark.django_db
def test_fs_plugin_paths(project_fs_empty, possible_actions):
    __, cmd, __, cmd_args = possible_actions
    project_fs_empty.fetch()
    pootle_path, fs_path = "FOO", "BAR"
    response = getattr(project_fs_empty, cmd)(
        pootle_path=pootle_path, fs_path=fs_path, **cmd_args)
    assert response.context.pootle_path == pootle_path
    assert response.context.fs_path == fs_path
    new_response = getattr(project_fs_empty, cmd)(
        response=response, pootle_path=pootle_path, fs_path=fs_path, **cmd_args)
    assert response.context.pootle_path == pootle_path
    assert response.context.fs_path == fs_path
    assert new_response is response
    state = response.context
    new_response = getattr(project_fs_empty, cmd)(
        state=state, pootle_path=pootle_path, fs_path=fs_path, **cmd_args)
    assert response.context.pootle_path == pootle_path
    assert response.context.fs_path == fs_path
    assert new_response.context is state


@pytest.mark.django_db
@pytest.mark.xfail(
    sys.platform == 'win32',
    reason="path mangling broken on windows")
def test_fs_plugin_response(localfs_envs, possible_actions, fs_response_map):
    state_type, plugin = localfs_envs
    action_name, action, command_args, plugin_kwargs = possible_actions
    stores_fs = None
    expected = fs_response_map[state_type].get(action_name)
    if not expected and action_name.endswith("_force"):
        expected = fs_response_map[state_type].get(action_name[:-6])
    plugin_response = getattr(plugin, action)(**plugin_kwargs)
    changes = []
    if not expected:
        assert plugin_response.made_changes is False
        return
    stores = plugin.resources.stores
    if not stores:
        stores_fs = plugin.resources.tracked
    if expected[0] in ["merged_from_pootle", "merged_from_fs"]:
        changes = ["_pulled", "_pushed", "_synced"]
    elif expected[0] == "added_from_pootle":
        changes = ["_added"]
    elif expected[0] == "pushed_to_fs":
        changes = ["_pushed", "_synced"]
    elif expected[0] == "pulled_to_pootle":
        changes = ["_pulled", "_synced"]
    elif expected[0] == "staged_for_merge_fs":
        changes = ["_merged", "_merge_fs"]
    elif expected[0] == "staged_for_merge_pootle":
        changes = ["_merged", "_merge_pootle"]
    elif expected[0] == "staged_for_removal":
        changes = ["_removed"]
    if changes:
        kwargs = {
            change: True
            for change in changes}
    else:
        kwargs = {}
    kwargs.update(
        dict(stores=stores,
             stores_fs=stores_fs))
    _test_dummy_response(
        action_name,
        plugin_response[expected[0]],
        **kwargs)


@pytest.mark.django_db
def test_plugin_instance_bad_args(project_fs_empty):
    fs_plugin = project_fs_empty.plugin

    with pytest.raises(TypeError):
        fs_plugin.__class__()

    with pytest.raises(TypeError):
        fs_plugin.__class__("FOO")


@pytest.mark.django_db
def test_plugin_fetch(project_fs_empty):
    assert project_fs_empty.is_cloned is False
    project_fs_empty.fetch()
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


@pytest.mark.django_db
def test_fs_plugin_sync_all():

    class SyncPlugin(Plugin):

        sync_order = []

        def push(self, response):
            self._push_response = response
            self.sync_order.append("plugin_push")
            return response

        def sync_merge(self, state, response, fs_path=None,
                       pootle_path=None, update=None):
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

    class DummyResources(object):
        file_hashes = {}
        pootle_revisions = {}

    state.resources = DummyResources()
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
        plugin.latest_hash

    with pytest.raises(NotImplementedError):
        plugin.fetch()

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
@pytest.mark.xfail(
    sys.platform == 'win32',
    reason="path mangling broken on windows")
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
def test_fs_plugin_cache_key(project_fs):
    plugin = project_fs
    assert plugin.ns == "pootle.fs.plugin"
    assert plugin.sw_version == PootleFSConfig.version
    assert (
        plugin.fs_revision
        == plugin.latest_hash)
    assert (
        plugin.sync_revision
        == revision.get(
            Project)(plugin.project).get(key="pootle.fs.sync"))
    assert (
        plugin.pootle_revision
        == revision.get(
            Directory)(plugin.project.directory).get(key="stats"))
    assert (
        plugin.cache_key
        == ("%s.%s.%s.%s"
            % (plugin.project.code,
               plugin.pootle_revision,
               plugin.sync_revision,
               plugin.fs_revision)))


@pytest.mark.django_db
def test_fs_plugin_fetch_bad(project0):
    plugin = FSPlugin(project0)
    plugin.clear_repo()

    with pytest.raises(FSStateError):
        plugin.add()

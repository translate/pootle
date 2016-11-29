# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import sys

import pytest


from pootle_fs.display import (
    FS_EXISTS_ACTIONS, STORE_EXISTS_ACTIONS,
    FS_EXISTS_STATES, STORE_EXISTS_STATES,
    ResponseDisplay, ResponseItemDisplay, ResponseTypeDisplay,
    StateDisplay, StateItemDisplay, StateTypeDisplay)
from pootle_fs.response import FS_RESPONSE
from pootle_fs.state import FS_STATE


@pytest.mark.django_db
def test_fs_response_display_instance(localfs_pootle_untracked):
    plugin = localfs_pootle_untracked
    response = plugin.add()
    display = ResponseDisplay(response)
    assert display.context == response
    assert display.sections == [
        rtype for rtype in response if response[rtype]]
    for section in display.sections:
        type_display = display.section(section)
        assert isinstance(type_display, ResponseTypeDisplay)
        assert type_display.context == display
        assert type_display.name == section
    result = ""
    for rtype in display.sections:
        result += str(display.section(rtype))
    assert result
    assert str(display) == "%s\n" % result


@pytest.mark.django_db
def test_fs_response_display_no_change(localfs_pootle_untracked):
    plugin = localfs_pootle_untracked
    assert str(ResponseDisplay(plugin.sync())) == "No changes made\n"


@pytest.mark.django_db
def test_fs_response_display_type_instance(localfs_pootle_untracked):
    plugin = localfs_pootle_untracked
    response = plugin.add()
    display = ResponseDisplay(response)
    section = ResponseTypeDisplay(display, "added_from_pootle")
    assert section.context == display
    assert section.name == "added_from_pootle"
    assert section.info == FS_RESPONSE["added_from_pootle"]
    assert section.description == section.info["description"]
    assert section.title == (
        "%s (%s)"
        % (section.info['title'],
           len(response[section.name])))
    assert (
        len(section.data)
        == len(section.items)
        == len(response["added_from_pootle"]))
    for i, item in enumerate(section.items):
        assert section.data[i] == item.item
        assert isinstance(item, ResponseItemDisplay)
    result = (
        "%s\n%s\n%s\n\n"
        % (section.title, "-" * len(section.title), section.description))
    for item in section.data:
        result += str(section.item_class(section, item))
    assert str(section) == "%s\n" % result


@pytest.mark.django_db
def test_fs_response_display_item_instance(localfs_pootle_untracked):
    plugin = localfs_pootle_untracked
    response = plugin.add()
    response_item = response["added_from_pootle"][0]
    item_display = ResponseItemDisplay(response, response_item)
    assert item_display.action_type == "added_from_pootle"
    assert item_display.state_item == response_item.fs_state
    assert item_display.file_exists is False
    assert item_display.store_exists is True
    assert item_display.pootle_path == response_item.pootle_path
    assert item_display.fs_path == "(%s)" % response_item.fs_path
    assert item_display.state_type == item_display.state_item.state_type
    result = (
        "  %s\n   <-->  %s\n"
        % (item_display.pootle_path, item_display.fs_path))
    assert str(item_display) == result


@pytest.mark.django_db
@pytest.mark.xfail(
    sys.platform == 'win32',
    reason="path mangling broken on windows")
def test_fs_response_display_item_fs_untracked(localfs_fs_untracked):
    plugin = localfs_fs_untracked
    response = plugin.add()
    response_item = response["added_from_fs"][0]
    item_display = ResponseItemDisplay(None, response_item)
    assert item_display.action_type == "added_from_fs"
    assert item_display.state_item == response_item.fs_state
    assert item_display.file_exists is True
    assert item_display.store_exists is False
    assert item_display.pootle_path == "(%s)" % response_item.pootle_path
    assert item_display.fs_path == response_item.fs_path
    assert item_display.state_type == item_display.state_item.state_type
    result = (
        "  %s\n   <-->  %s\n"
        % (item_display.pootle_path, item_display.fs_path))
    assert str(item_display) == result


def test_fs_response_display_item_existence(fs_responses, fs_states):

    class DummyResponseItem(object):

        @property
        def action_type(self):
            return fs_responses

    class ResponseItemDisplayTestable(ResponseItemDisplay):

        @property
        def state_type(self):
            return fs_states

    file_exists = (
        fs_responses in FS_EXISTS_ACTIONS
        or (fs_states
            in ["conflict", "conflict_untracked"])
        or (fs_responses == "staged_for_removal"
            and (fs_states
                 in ["fs_untracked", "pootle_removed"])))
    store_exists = (
        fs_responses in STORE_EXISTS_ACTIONS
        or (fs_states
            in ["conflict", "conflict_untracked"])
        or (fs_responses == "staged_for_removal"
            and (fs_states
                 in ["pootle_untracked", "fs_removed"])))
    fs_added = (
        fs_responses == "added_from_fs"
        and fs_states not in ["conflict", "conflict_untracked"])
    pootle_added = (
        fs_responses == "added_from_pootle"
        and fs_states not in ["conflict", "conflict_untracked"])
    item_display = ResponseItemDisplayTestable({}, DummyResponseItem())
    assert item_display.file_exists == file_exists
    assert item_display.store_exists == store_exists
    assert item_display.fs_added == fs_added
    assert item_display.pootle_added == pootle_added


@pytest.mark.django_db
def test_fs_state_display_instance(localfs_pootle_untracked):
    plugin = localfs_pootle_untracked
    state = plugin.state()
    display = StateDisplay(state)
    assert display.context == state
    assert display.sections == [
        state_type for state_type
        in display.context
        if display.context[state_type]]


@pytest.mark.django_db
def test_fs_state_display_type_instance(localfs_pootle_untracked):
    plugin = localfs_pootle_untracked
    state = plugin.state()
    display = StateDisplay(state)
    section = StateTypeDisplay(display, "pootle_untracked")
    assert section.context == display
    assert section.name == "pootle_untracked"
    assert section.info == FS_STATE[section.name]
    assert section.title == (
        "%s (%s)"
        % (section.info['title'],
           len(section.context.context[section.name])))


@pytest.mark.django_db
def test_fs_display_state_item_instance(localfs_pootle_untracked):
    plugin = localfs_pootle_untracked
    state_item = plugin.state()["pootle_untracked"][0]
    item_display = StateItemDisplay(None, state_item)
    assert item_display.item == state_item
    assert item_display.state_type == "pootle_untracked"
    assert item_display.file is None
    assert item_display.file_exists is False
    assert item_display.store_exists is True
    assert item_display.tracked is False


@pytest.mark.django_db
def test_fs_display_state_item_instance_file(localfs_pootle_untracked):
    plugin = localfs_pootle_untracked
    state_item = plugin.state()["pootle_untracked"][0]
    item_display = StateItemDisplay(None, state_item)
    assert item_display.item.store_fs is None
    assert item_display.tracked is False
    assert item_display.file is None
    plugin.add()
    state_item = plugin.state()["pootle_staged"][0]
    item_display = StateItemDisplay(None, state_item)
    assert item_display.file == state_item.store_fs.file


@pytest.mark.django_db
@pytest.mark.xfail(
    sys.platform == 'win32',
    reason="path mangling broken on windows")
def test_fs_display_state_item_instance_fs_untracked(localfs_fs_untracked):
    plugin = localfs_fs_untracked
    state_item = plugin.state()["fs_untracked"][0]
    item_display = StateItemDisplay(None, state_item)
    assert item_display.item == state_item
    assert item_display.state_type == "fs_untracked"
    assert item_display.file is None
    assert item_display.file_exists is True
    assert item_display.store_exists is False
    assert item_display.tracked is False


def test_fs_display_state_item_existence(fs_states):

    class DummyStateItem(object):
        pass

    class DummyFile(object):
        file_exists = False
        store_exists = False

    class StateItemDisplayTestable(StateItemDisplay):

        @property
        def state_type(self):
            return fs_states

        file = DummyFile()

    item_display = StateItemDisplayTestable({}, DummyStateItem())
    if fs_states == "remove":
        assert item_display.file_exists is False
        assert item_display.store_exists is False
        item_display.file.file_exists = True
        assert item_display.file_exists is True
        assert item_display.store_exists is False
        item_display.file.store_exists = True
        assert item_display.store_exists is True
    else:
        assert item_display.file_exists == (fs_states in FS_EXISTS_STATES)
        assert item_display.store_exists == (fs_states in STORE_EXISTS_STATES)

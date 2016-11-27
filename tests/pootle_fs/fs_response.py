#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from pootle.core.state import ItemState, State
from pootle_fs.models import StoreFS
from pootle_fs.response import (
    FS_RESPONSE, ProjectFSItemResponse, ProjectFSResponse)
from pootle_project.models import Project
from pootle_store.models import Store


class DummyContext(object):

    def __str__(self):
        return "<DummyContext object>"


class DummyFSItemState(ItemState):

    @property
    def pootle_path(self):
        if "pootle_path" in self.kwargs:
            return self.kwargs["pootle_path"]
        elif self.store_fs:
            return self.store_fs.pootle_path
        elif self.store:
            return self.store.pootle_path

    @property
    def fs_path(self):
        if "fs_path" in self.kwargs:
            return self.kwargs["fs_path"]
        elif self.store_fs:
            return self.store_fs.path

    @property
    def store(self):
        if "store" in self.kwargs:
            return self.kwargs["store"]
        elif self.store_fs:
            return self.store_fs.store

    @property
    def store_fs(self):
        return self.kwargs.get("store_fs")


class DummyFSState(State):
    """The pootle_fs State can create ItemStates with
    - a store_fs (that has a store)
    - a store_fs (that has no store)
    - a store and an fs_path
    - a pootle_path and an fs_path
    """

    item_state_class = DummyFSItemState

    def state_fs_staged(self, **kwargs):
        for store_fs in kwargs.get("fs_staged", []):
            yield dict(store_fs=store_fs)

    def state_fs_ahead(self, **kwargs):
        for store_fs in kwargs.get("fs_ahead", []):
            yield dict(store_fs=store_fs)

    def state_fs_untracked(self, **kwargs):
        for fs_path, pootle_path in kwargs.get("fs_untracked", []):
            yield dict(fs_path=fs_path, pootle_path=pootle_path)

    def state_pootle_untracked(self, **kwargs):
        for fs_path, store in kwargs.get("pootle_untracked", []):
            yield dict(fs_path=fs_path, store=store)


@pytest.mark.django_db
def test_fs_response_instance():
    context = DummyContext()
    resp = ProjectFSResponse(context)
    assert resp.context == context
    assert resp.response_types == FS_RESPONSE.keys()
    assert resp.has_failed is False
    assert resp.made_changes is False
    assert list(resp.failed()) == []
    assert list(resp.completed()) == []
    assert str(resp) == (
        "<ProjectFSResponse(<DummyContext object>): No changes made>")
    assert list(resp) == []
    with pytest.raises(KeyError):
        resp["DOES_NOT_EXIST"]


def _test_item(item, item_state):
    assert isinstance(item, ProjectFSItemResponse)
    assert item.kwargs["fs_state"] == item_state
    assert item.fs_state == item_state
    assert item.failed is False
    assert item.fs_path == item.fs_state.fs_path
    assert item.pootle_path == item.fs_state.pootle_path
    assert item.store_fs == item.fs_state.store_fs
    assert item.store == item.fs_state.store
    assert (
        str(item)
        == ("<ProjectFSItemResponse(<DummyContext object>): %s "
            "%s::%s>" % (item.action_type, item.pootle_path, item.fs_path)))


def _test_fs_response(expected=2, **kwargs):
    action_type = kwargs.pop("action_type")
    state_type = kwargs.pop("state_type")
    resp = ProjectFSResponse(DummyContext())
    state = DummyFSState(DummyContext(), **kwargs)
    for fs_state in state[state_type]:
        resp.add(action_type, fs_state=fs_state)
    assert resp.has_failed is False
    assert resp.made_changes is True
    assert resp.response_types == FS_RESPONSE.keys()
    assert len(list(resp.completed())) == 2
    assert list(resp.failed()) == []
    assert action_type in resp
    assert str(resp) == (
        "<ProjectFSResponse(<DummyContext object>): %s: %s>"
        % (action_type, expected))
    for i, item in enumerate(resp[action_type]):
        _test_item(item, state[state_type][i])


@pytest.mark.django_db
def test_fs_response_path_items(settings, tmpdir):
    settings.POOTLE_FS_WORKING_PATH = os.path.join(str(tmpdir),
                                                   "fs_response_test")
    project = Project.objects.get(code="project0")
    fs_untracked = []
    for i in range(0, 2):
        fs_untracked.append(
            ("/some/fs/fs_untracked_%s.po" % i,
             "/language0/%s/fs_untracked_%s.po" % (project.code, i)))
    _test_fs_response(
        fs_untracked=fs_untracked,
        action_type="added_from_fs",
        state_type="fs_untracked")


@pytest.mark.django_db
def test_fs_response_store_items(settings, tmpdir):
    settings.POOTLE_FS_WORKING_PATH = os.path.join(str(tmpdir),
                                                   "fs_response_test")
    project = Project.objects.get(code="project0")

    pootle_untracked = []
    for i in range(0, 2):
        pootle_untracked.append(
            ("/some/fs/pootle_untracked_%s.po" % i,
             Store.objects.create_by_path(
                 "/language0/%s/pootle_untracked_%s.po" % (project.code, i))))
    _test_fs_response(
        pootle_untracked=pootle_untracked,
        action_type="added_from_pootle",
        state_type="pootle_untracked")


@pytest.mark.django_db
def test_fs_response_store_fs_items(settings, tmpdir):
    settings.POOTLE_FS_WORKING_PATH = os.path.join(str(tmpdir),
                                                   "fs_response_test")
    project = Project.objects.get(code="project0")
    fs_ahead = []
    for i in range(0, 2):
        pootle_path = "/language0/%s/fs_ahead_%s.po" % (project.code, i)
        fs_path = "/some/fs/fs_ahead_%s.po" % i
        fs_ahead.append(
            StoreFS.objects.create(
                store=Store.objects.create_by_path(pootle_path),
                path=fs_path))
    _test_fs_response(
        fs_ahead=fs_ahead,
        action_type="pulled_to_pootle",
        state_type="fs_ahead")


@pytest.mark.django_db
def test_fs_response_store_fs_no_store_items(settings, tmpdir):
    settings.POOTLE_FS_WORKING_PATH = os.path.join(str(tmpdir),
                                                   "fs_response_test")
    project = Project.objects.get(code="project0")
    fs_staged = []
    for i in range(0, 2):
        pootle_path = "/language0/%s/fs_staged_%s.po" % (project.code, i)
        fs_path = "/some/fs/fs_staged_%s.po" % i
        fs_staged.append(
            StoreFS.objects.create(
                pootle_path=pootle_path,
                path=fs_path))
    _test_fs_response(
        fs_staged=fs_staged,
        action_type="pulled_to_pootle",
        state_type="fs_staged")

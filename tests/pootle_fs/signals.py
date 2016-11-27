# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.dispatch import receiver

from pootle_fs.signals import (
    fs_pre_push, fs_post_push, fs_pre_pull, fs_post_pull)


@pytest.mark.django_db
def test_fs_pull_signal(project_fs):

    project_fs.add(force=True)
    state = project_fs.state()

    class Success(object):
        expected = len(state["fs_staged"]) + len(state["fs_ahead"])
        pre_pull_called = False
        post_pull_called = False
    success = Success()

    @receiver(fs_pre_pull)
    def fs_pre_pull_handler(**kwargs):
        assert kwargs["plugin"] is project_fs.plugin
        assert "No changes made" in str(kwargs["response"])
        assert "pulled_to_pootle" not in kwargs["response"]
        # we see the original state
        assert (
            success.expected
            == (len(kwargs["state"]["fs_staged"])
                + len(kwargs["state"]["fs_ahead"])))
        success.pre_pull_called = True

    @receiver(fs_post_pull)
    def fs_post_pull_handler(**kwargs):
        assert kwargs["plugin"] is project_fs.plugin
        # we still see the original state
        assert (
            success.expected
            == (len(kwargs["state"]["fs_staged"])
                + len(kwargs["state"]["fs_ahead"])))
        # but the response has been updated
        assert (
            success.expected
            == len(kwargs["response"]["pulled_to_pootle"]))
        success.post_pull_called = True
        success.response = kwargs["response"]

    assert project_fs.sync_pull() == success.response
    assert success.pre_pull_called is True
    assert success.post_pull_called is True


@pytest.mark.django_db
def test_fs_push_signal(project_fs):

    project_fs.add(force=True)
    state = project_fs.state()

    class Success(object):
        expected = len(state["pootle_staged"]) + len(state["pootle_ahead"])
        pre_push_called = False
        post_push_called = False
    success = Success()

    @receiver(fs_pre_push)
    def fs_pre_push_handler(**kwargs):
        assert kwargs["plugin"] is project_fs.plugin
        assert "No changes made" in str(kwargs["response"])
        assert "pushed_to_pootle" not in kwargs["response"]
        # we see the original state
        assert (
            success.expected
            == (len(kwargs["state"]["pootle_staged"])
                + len(kwargs["state"]["pootle_ahead"])))
        success.pre_push_called = True

    @receiver(fs_post_push)
    def fs_post_push_handler(**kwargs):
        assert kwargs["plugin"] is project_fs.plugin
        # we still see the original state
        assert (
            success.expected
            == (len(kwargs["state"]["pootle_staged"])
                + len(kwargs["state"]["pootle_ahead"])))
        # but the response has been updated
        assert (
            success.expected
            == len(kwargs["response"]["pushed_to_fs"]))
        success.post_push_called = True
        success.response = kwargs["response"]

    assert project_fs.sync_push() == success.response
    assert success.pre_push_called is True
    assert success.post_push_called is True

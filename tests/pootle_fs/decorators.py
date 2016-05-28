#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.dispatch import receiver

from pootle.core.state import State
from pootle.core.response import Response
from pootle_fs.decorators import emits_state, responds_to_state
from pootle_fs.signals import (
    fs_post_pull, fs_post_push, fs_pre_pull, fs_pre_push)


class PluginState(State):
    pass


class PluginResponse(Response):
    pass


class DummyPlugin(object):

    def state(self, **kwargs):
        return PluginState(self, **kwargs)

    def response(self, state, **kwargs):
        return PluginResponse(state, **kwargs)


class MyPlugin(DummyPlugin):

    @responds_to_state
    def respond_to_state(self, state, response, **kwargs):
        return state, response, kwargs

    @emits_state(pre=fs_pre_pull)
    def emit_state_pre(self, state, response, **kwargs):
        return state, response, kwargs

    @emits_state(pre=fs_post_pull)
    def emit_state_post(self, state, response, **kwargs):
        return state, response, kwargs

    @emits_state(pre=fs_pre_push, post=fs_post_push)
    def emit_state_both(self, state, response, **kwargs):
        return state, response, kwargs


@pytest.mark.django_db
def test_fs_deco_emits_pre():
    plugin = MyPlugin()
    plugin_state = plugin.state()
    plugin_response = plugin.response(plugin_state)

    class Emitted(object):
        pass

    emitted = Emitted()

    @receiver(fs_pre_pull)
    def received(state, response, **kwargs):
        emitted.state = state
        emitted.response = response
        emitted.kwargs = kwargs

    state, response, kwargs = plugin.emit_state_pre(
        plugin_state, plugin_response, foo="bar")

    assert state is emitted.state is plugin_state
    assert response is emitted.response is plugin_response
    assert kwargs == dict(foo="bar")
    assert emitted.kwargs["plugin"] == plugin
    assert emitted.kwargs["sender"] == plugin.__class__


@pytest.mark.django_db
def test_fs_deco_emits_post():
    plugin = MyPlugin()
    plugin_state = plugin.state()
    plugin_response = plugin.response(plugin_state)

    class Emitted(object):
        pass

    emitted = Emitted()

    @receiver(fs_post_pull)
    def received(state, response, **kwargs):
        emitted.state = state
        emitted.response = response
        emitted.kwargs = kwargs

    state, response, kwargs = plugin.emit_state_post(
        plugin_state, plugin_response, foo="bar")

    assert state is emitted.state is plugin_state
    assert response is emitted.response is plugin_response
    assert kwargs == dict(foo="bar")
    assert emitted.kwargs["plugin"] == plugin
    assert emitted.kwargs["sender"] == plugin.__class__


@pytest.mark.django_db
def test_fs_deco_emits_both():
    plugin = MyPlugin()
    plugin_state = plugin.state()
    plugin_response = plugin.response(plugin_state)

    class Emitted(object):
        pass

    emitted_pre = Emitted()
    emitted_post = Emitted()

    @receiver(fs_pre_push)
    def received_pre(state, response, **kwargs):
        emitted_pre.state = state
        emitted_pre.response = response
        emitted_pre.kwargs = kwargs

    @receiver(fs_post_push)
    def received_post(state, response, **kwargs):
        emitted_post.state = state
        emitted_post.response = response
        emitted_post.kwargs = kwargs

    state, response, kwargs = plugin.emit_state_both(
        plugin_state, plugin_response, foo="bar")

    assert (
        state is emitted_pre.state
        is emitted_post.state
        is plugin_state)
    assert (
        response is emitted_pre.response
        is emitted_post.response
        is plugin_response)
    assert kwargs == dict(foo="bar")
    assert emitted_pre.kwargs["plugin"] == plugin
    assert emitted_pre.kwargs["sender"] == plugin.__class__
    assert emitted_post.kwargs["plugin"] == plugin
    assert emitted_post.kwargs["sender"] == plugin.__class__


@pytest.mark.django_db
def test_fs_deco_responds_to_state():
    plugin = MyPlugin()
    state, response, kwargs = plugin.respond_to_state()
    assert isinstance(state, PluginState)
    assert isinstance(response, PluginResponse)
    assert state.context == plugin
    assert response.context == state
    assert state.kwargs["pootle_path"] is None
    assert state.kwargs["fs_path"] is None
    assert len(kwargs) == 0
    assert len(state.kwargs) == 2


@pytest.mark.django_db
def test_fs_deco_responds_to_state_pootle_path():
    plugin = MyPlugin()
    state, response, kwargs = plugin.respond_to_state(pootle_path="/foo")
    assert state.kwargs["pootle_path"] == "/foo"
    assert state.kwargs["fs_path"] is None
    assert kwargs["pootle_path"] == "/foo"
    assert len(kwargs) == 1
    assert len(state.kwargs) == 2


@pytest.mark.django_db
def test_fs_deco_responds_to_state_fs_path():
    plugin = MyPlugin()
    state, response, kwargs = plugin.respond_to_state(fs_path="/foo")
    assert state.kwargs["pootle_path"] is None
    assert state.kwargs["fs_path"] == "/foo"
    assert kwargs["fs_path"] == "/foo"
    assert len(kwargs) == 1
    assert len(state.kwargs) == 2


@pytest.mark.django_db
def test_fs_deco_responds_to_state_kwargs():
    plugin = MyPlugin()
    state, response, kwargs = plugin.respond_to_state(foo="/foo")
    assert state.kwargs["pootle_path"] is None
    assert state.kwargs["fs_path"] is None
    assert kwargs["foo"] == "/foo"
    assert len(kwargs) == 1
    assert len(state.kwargs) == 2


@pytest.mark.django_db
def test_fs_deco_responds_to_state_w_state():
    plugin = MyPlugin()
    plugin_state = plugin.state()
    state, response, kwargs = plugin.respond_to_state(
        foo="/foo", state=plugin_state)
    assert plugin_state is state
    assert "state" not in kwargs
    assert "state" not in state.kwargs

    state, response, kwargs = plugin.respond_to_state(
        plugin_state, foo="/foo")
    assert plugin_state is state
    assert "state" not in kwargs
    assert "state" not in state.kwargs


@pytest.mark.django_db
def test_fs_deco_responds_to_state_w_response():
    plugin = MyPlugin()
    plugin_state = plugin.state()
    plugin_response = plugin.response(plugin_state)
    state, response, kwargs = plugin.respond_to_state(
        foo="/foo", response=plugin_response)
    assert plugin_response is response
    assert "response" not in kwargs
    assert "response" not in state.kwargs

    state, response, kwargs = plugin.respond_to_state(
        plugin_state, plugin_response, foo="/foo")
    assert plugin_response is response
    assert "response" not in kwargs
    assert "response" not in state.kwargs


@pytest.mark.django_db
def test_fs_deco_responds_to_state_w_state_response():
    plugin = MyPlugin()
    plugin_state = plugin.state()
    plugin_response = plugin.response(plugin_state)
    state, response, kwargs = plugin.respond_to_state(
        foo="/foo", state=plugin_state, response=plugin_response)
    assert plugin_response is response
    assert "response" not in kwargs
    assert "response" not in state.kwargs
    assert plugin_state is state
    assert "state" not in kwargs
    assert "state" not in state.kwargs
    state, response, kwargs = plugin.respond_to_state(
        plugin_state, foo="/foo", response=plugin_response)
    assert plugin_response is response
    assert "response" not in kwargs
    assert "response" not in state.kwargs
    assert plugin_state is state
    assert "state" not in kwargs
    assert "state" not in state.kwargs
    state, response, kwargs = plugin.respond_to_state(
        plugin_state, plugin_response, foo="/foo")
    assert plugin_response is response
    assert "response" not in kwargs
    assert "response" not in state.kwargs
    assert plugin_state is state
    assert "state" not in kwargs
    assert "state" not in state.kwargs

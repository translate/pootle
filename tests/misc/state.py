#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.state import State, ItemState


class DummyContext(object):

    def __str__(self):
        return "<DummyContext object>"


def test_state_instance():

    context = DummyContext()
    state = State(context)

    assert state.context == context
    assert state.__state__ == {}
    assert state.prefix == "state"
    assert state.has_changed is False
    assert state.states == []
    assert "x" not in state
    assert list(state) == []
    assert state.item_state_class == ItemState
    assert str(state) == (
        "<State(<DummyContext object>): Nothing to report>")


def test_state_states():
    """By default the State class will automagically find any
    methods that start with `state_` and create a list of states
    from these.

    In a descendant class you can manually set the states, in order to
    control which state methods are called and in what order. This tests that
    """

    class ContextualState(State):

        @property
        def states(self):
            return ["foo", "bar", "empty"]

        def state_foo(self, **kwargs):
            for x in [1, 2, 3]:
                yield {str(x): x}

        def state_bar(self, **kwargs):
            for x in [4, 5, 6, 7, 8, 9]:
                yield {str(x): x}

        def state_baz(self, **kwargs):
            yield dict(never="called")

        def state_empty(self, **kwargs):
            return []

    context = DummyContext()
    state = ContextualState(context)

    assert str(state) == (
        "<ContextualState(<DummyContext object>): foo: 3, bar: 6>")
    assert state.context == context

    assert sorted(state.__state__.keys()) == ["bar", "empty", "foo"]
    assert "empty" in state.__state__
    assert "baz" not in state.__state__

    assert state["empty"] == []
    with pytest.raises(KeyError):
        state["baz"]

    assert sorted(state) == ["bar", "foo"]
    assert state.has_changed is True
    assert state.states == ["foo", "bar", "empty"]
    assert len(state["foo"]) == 3
    assert isinstance(state["foo"][0], state.item_state_class)
    assert state["foo"][0].kwargs == {"1": 1}
    assert state["foo"][0].state == state
    assert state["foo"][0].state_type == "foo"


def test_state_all_states():

    class ContextualState(State):

        def state_foo(self, **kwargs):
            for x in [1, 2, 3]:
                yield {str(x): x}

        def state_bar(self, **kwargs):
            for x in [4, 5, 6, 7, 8, 9]:
                yield {str(x): x}

        def state_baz(self, **kwargs):
            for x in [10, 11, 12]:
                yield {str(x): x}

        def state_empty(self, **kwargs):
            return []

    context = DummyContext()
    state = ContextualState(context)
    assert str(state) == (
        "<ContextualState(<DummyContext object>): bar: 6, baz: 3, foo: 3>")
    assert state.context == context

    assert sorted(state.__state__.keys()) == ['bar', 'baz', 'empty', 'foo']
    assert "baz" in state.__state__
    assert sorted(state) == ["bar", "baz", "foo"]
    assert state.has_changed is True
    assert state.states == ['bar', 'baz', 'empty', 'foo']
    assert len(state["baz"]) == 3


def test_state_properties():

    class ContextualState(State):

        @property
        def state_foo(self):
            for x in self.kwargs["baz"]:
                yield {"foo%s" % x: x}

        @property
        def state_bar(self):
            for x in self.kwargs["baz"]:
                yield {"bar%s" % x: x}

    context = DummyContext()
    state = ContextualState(context, baz=[1, 2])
    assert state["foo"][0].kwargs.items() == [("foo1", 1)]
    assert state["foo"][1].kwargs.items() == [("foo2", 2)]
    assert state["bar"][0].kwargs.items() == [("bar1", 1)]
    assert state["bar"][1].kwargs.items() == [("bar2", 2)]


def test_state_item_kwargs():

    class ContextualState(State):

        @property
        def state_foo(self):
            for x in self.kwargs["baz"]:
                yield {"foo%s" % x: x}

        def state_bar(self, **kwargs):
            for x in self.kwargs["baz"]:
                yield {"bar%s" % x: x}

    context = DummyContext()
    state = ContextualState(context, baz=[1, 2])
    assert state["foo"][0].kwargs.items() == [("foo1", 1)]
    assert state["foo"][0].foo1 == 1
    assert not hasattr(state["foo"][0], "foo2")
    assert state["foo"][1].kwargs.items() == [("foo2", 2)]
    assert state["foo"][1].foo2 == 2
    assert not hasattr(state["foo"][1], "foo3")
    assert state["bar"][0].kwargs.items() == [("bar1", 1)]
    assert state["bar"][0].bar1 == 1
    assert not hasattr(state["bar"][0], "bar2")
    assert state["bar"][1].kwargs.items() == [("bar2", 2)]
    assert state["bar"][1].bar2 == 2
    assert not hasattr(state["bar"][1], "bar3")


def test_state_bad():
    # requires a context
    with pytest.raises(TypeError):
        State()

    class ContextualState(State):

        states = 3

    # context.states must be iterable if set
    with pytest.raises(TypeError):
        ContextualState(DummyContext())

    class ContextualState(State):

        def state_foo(self, **kwargs):
            yield []

    # context.state_* methods should yield dict-like object
    with pytest.raises(TypeError):
        ContextualState(DummyContext())


def test_state_item_instance():

    class DummyContext(object):

        def __str__(self):
            return "<DummyContext object>"

    context = DummyContext()
    state = State(context)
    item = ItemState(state, "foo")
    assert item.state == state
    assert item.state_type == "foo"
    assert str(item) == (
        "<ItemState(<DummyContext object>): foo {}>")
    assert item == ItemState(state, "foo")


def test_state_kwargs():

    class ContextualState(State):

        def state_foo(self, **kwargs):
            yield kwargs

    kwargs = dict(kwarg1="kw1", kwarg2="kw2")
    state = ContextualState(DummyContext(), **kwargs)
    assert state.kwargs == kwargs
    assert state["foo"][0].kwargs == kwargs
    state["foo"][0].kwarg1 == "kw1"
    state["foo"][0].kwarg2 == "kw2"


def test_state_item_bad():

    class ContextualState(State):

        def state_foo(self, **kwargs):
            for x in [1, 2, 3]:
                yield {str(x): x}

    # needs state and state_type arg
    with pytest.raises(TypeError):
        ItemState()

    # needs state_type arg
    with pytest.raises(TypeError):
        ItemState(ContextualState(DummyContext()))

    assert ItemState(ContextualState(DummyContext()), "foo")


def test_state_reload():

    class ContextualState(State):

        def state_foo(self, **kwargs):
            yield dict(result=(2 * self.context.base))

    context = DummyContext()
    context.base = 2
    state = ContextualState(context)
    assert state["foo"][0].kwargs["result"] == 4
    context.base = 3
    assert state["foo"][0].kwargs["result"] == 4
    state.reload()
    assert state["foo"][0].kwargs["result"] == 6
    state.clear_cache()
    assert list(state) == []

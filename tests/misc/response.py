#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.response import ItemResponse, Response


class DummyContext(object):

    def __str__(self):
        return "<DummyContext object>"


def test_response_instance():
    context = DummyContext()
    resp = Response(context)
    assert resp.context == context
    assert resp.response_types == []
    assert resp.has_failed is False
    assert resp.made_changes is False
    assert list(resp.failed()) == []
    assert list(resp.completed()) == []
    assert str(resp) == "<Response(<DummyContext object>): No changes made>"
    assert list(resp) == []
    with pytest.raises(KeyError):
        resp["DOES_NOT_EXIST"]


def test_response_completed():
    resp = Response(DummyContext())
    resp.add("foo_response", completed=True)
    assert resp.has_failed is False
    assert resp.made_changes is True
    assert resp.response_types == ["foo_response"]
    assert len(list(resp.completed())) == 1
    assert list(resp.failed()) == []
    assert "foo_response" in resp
    assert isinstance(resp["foo_response"][0], ItemResponse)
    assert str(resp) == "<Response(<DummyContext object>): foo_response: 1>"
    resp.add("foo_response")
    assert resp.has_failed is False
    assert resp.made_changes is True
    assert resp.response_types == ["foo_response"]
    assert len(list(resp.completed())) == 2
    assert list(resp.failed()) == []
    assert "foo_response" in resp
    assert isinstance(resp["foo_response"][0], ItemResponse)
    assert isinstance(resp["foo_response"][1], ItemResponse)
    assert str(resp) == "<Response(<DummyContext object>): foo_response: 2>"
    resp.add("other_response")
    assert resp.has_failed is False
    assert resp.made_changes is True
    assert sorted(resp.response_types) == ["foo_response", "other_response"]
    assert len(list(resp.completed())) == 3
    assert list(resp.failed()) == []
    assert "foo_response" in resp
    assert "other_response" in resp
    assert isinstance(resp["other_response"][0], ItemResponse)
    assert isinstance(resp["foo_response"][0], ItemResponse)
    assert isinstance(resp["foo_response"][1], ItemResponse)
    assert str(resp).startswith("<Response(<DummyContext object>): ")
    assert "foo_response: 2" in str(resp)
    assert "other_response: 1" in str(resp)
    assert "FAIL" not in str(resp)


def test_response_failed():
    resp = Response(DummyContext())
    resp.add("foo_response", complete=False)
    assert resp.has_failed is True
    assert resp.made_changes is False
    assert resp.response_types == ["foo_response"]
    assert len(list(resp.failed())) == 1
    assert list(resp.completed()) == []
    assert "foo_response" in resp
    assert isinstance(resp["foo_response"][0], ItemResponse)
    assert str(resp) == "<Response(<DummyContext object>): FAIL No changes made>"

    # now add some successful responses
    resp.add("foo_response")
    assert resp.has_failed is True
    assert resp.made_changes is True
    assert len(list(resp.failed())) == 1
    assert len(list(resp.completed())) == 1
    assert str(resp) == "<Response(<DummyContext object>): FAIL foo_response: 1>"

    resp.add("other_response")
    assert resp.has_failed is True
    assert resp.made_changes is True
    assert len(list(resp.failed())) == 1
    assert len(list(resp.completed())) == 2
    assert str(resp).startswith("<Response(<DummyContext object>): FAIL ")
    assert "foo_response: 1" in str(resp)
    assert "other_response: 1" in str(resp)
    assert str(resp["foo_response"][0]).startswith(
        "<ItemResponse(<Response(<DummyContext object>): FAIL ")
    assert str(resp["foo_response"][0]).endswith(
        "foo_response FAILED>")
    # clear cache, response_types are remembered
    resp.clear_cache()
    assert str(resp) == "<Response(<DummyContext object>): No changes made>"
    assert resp.__responses__["foo_response"] == []
    assert resp.__responses__["other_response"] == []


def test_response_kwargs():
    resp = Response(DummyContext())
    resp.add("foo_response", foo="foo1", bar="bar1")
    assert resp.has_failed is False
    assert resp.made_changes is True
    assert resp.response_types == ["foo_response"]
    assert len(list(resp.completed())) == 1
    assert list(resp.failed()) == []
    assert "foo_response" in resp
    assert isinstance(resp["foo_response"][0], ItemResponse)
    assert str(resp) == "<Response(<DummyContext object>): foo_response: 1>"
    assert resp["foo_response"][0].kwargs["foo"] == "foo1"
    assert resp["foo_response"][0].kwargs["bar"] == "bar1"
    assert str(resp["foo_response"][0]).startswith(
        "<ItemResponse(<Response(<DummyContext object>): foo_response: 1>): "
        "foo_response")
    assert "'foo': 'foo1'" in str(resp["foo_response"][0])
    assert "'bar': 'bar1'" in str(resp["foo_response"][0])


def test_response_msg():
    resp = Response(DummyContext())
    resp.add("foo_response", msg="Response message")
    assert resp.has_failed is False
    assert resp.made_changes is True
    assert resp.response_types == ["foo_response"]
    assert len(list(resp.completed())) == 1
    assert list(resp.failed()) == []
    assert "foo_response" in resp
    assert isinstance(resp["foo_response"][0], ItemResponse)
    assert str(resp) == "<Response(<DummyContext object>): foo_response: 1>"
    assert str(resp["foo_response"][0]) == (
        "<ItemResponse(<Response(<DummyContext object>): foo_response: 1>): "
        "foo_response Response message>")

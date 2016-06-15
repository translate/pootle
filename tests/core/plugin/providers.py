# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.plugin import provider
from pootle.core.plugin.delegate import Provider
from pootle.core.plugin.exceptions import StopProviding
from pootle.core.plugin.results import GatheredDict, GatheredList


def test_provider():

    provider_test = Provider(providing_args=["foo"])

    @provider(provider_test)
    def provider_for_test(*args, **kwargs):
        return dict(result=2)

    results = provider_test.gather()
    assert isinstance(results, GatheredDict)
    assert results["result"] == 2


def test_no_providers():

    provider_test = Provider(providing_args=["foo"])

    results = provider_test.gather()
    assert isinstance(results, GatheredDict)
    assert results.keys() == []


def test_provider_with_arg():

    provider_test = Provider(providing_args=["foo"])

    @provider(provider_test)
    def provider_for_test(*args, **kwargs):
        return dict(result=kwargs["foo"])

    results = provider_test.gather(None, foo=3)
    assert isinstance(results, GatheredDict)
    assert results["result"] == 3


def test_provider_with_sender():

    provider_test = Provider(providing_args=["foo"])

    @provider(provider_test, sender=str)
    def provider_for_test(sender, *args, **kwargs):
        return dict(result=kwargs["foo"])

    results = provider_test.gather(str, foo="BOOM")
    assert isinstance(results, GatheredDict)
    assert results["result"] == "BOOM"


def test_provider_with_sender_int():

    provider_test = Provider(providing_args=["foo"])

    @provider(provider_test)
    def provider_for_test(*args, **kwargs):
        return dict(result=kwargs["foo"] * 7)

    results = provider_test.gather(int, foo=3)
    assert isinstance(results, GatheredDict)
    assert results["result"] == 21


def test_provider_with_sender_multi():

    provider_test = Provider(providing_args=["foo"])

    @provider(provider_test)
    def provider_for_test(sender, *args, **kwargs):
        if sender is str:
            return dict(result=int(kwargs["foo"]) * 7)
        return dict(result=kwargs["foo"] * 7)

    results = provider_test.gather(str, foo="3")
    assert isinstance(results, GatheredDict)
    assert results["result"] == 21

    results = provider_test.gather(int, foo=3)
    assert isinstance(results, GatheredDict)
    assert results["result"] == 21


def test_provider_handle_multi_decorators():

    provider_test = Provider(providing_args=["foo"])
    provider_test_2 = Provider(providing_args=["foo"])

    @provider([provider_test, provider_test_2], sender=str)
    def provider_for_test(sender, *args, **kwargs):
        return dict(result="BOOM: %s" % kwargs["foo"])

    results = provider_test.gather(str, foo="1")
    assert isinstance(results, GatheredDict)
    assert results["result"] == "BOOM: 1"

    results = provider_test_2.gather(str, foo="2")
    assert isinstance(results, GatheredDict)
    assert results["result"] == "BOOM: 2"


def test_provider_handle_multi_providers():

    provider_test = Provider()

    @provider(provider_test)
    def provider_for_test(sender, *args, **kwargs):
        return dict(result1=1)

    @provider(provider_test)
    def provider_for_test_2(sender, *args, **kwargs):
        return dict(result2=2)

    results = provider_test.gather()
    assert isinstance(results, GatheredDict)
    assert results["result1"] == 1
    assert results["result2"] == 2


def test_provider_handle_null_provider():

    provider_test = Provider()

    @provider(provider_test)
    def provider_for_test(sender, *args, **kwargs):
        return dict(result1=1)

    @provider(provider_test)
    def provider_for_test_2(sender, *args, **kwargs):
        return None

    @provider(provider_test)
    def provider_for_test_3(sender, *args, **kwargs):
        return dict(result3=3)

    results = provider_test.gather()
    assert isinstance(results, GatheredDict)
    assert results["result1"] == 1
    assert "result2" not in results
    assert results["result3"] == 3


def test_provider_handle_bad_providers():

    provider_test = Provider()

    @provider(provider_test)
    def provider_for_test(sender, *args, **kwargs):
        return dict(result1=1)

    @provider(provider_test)
    def provider_for_test_2(sender, *args, **kwargs):
        return 3

    @provider(provider_test)
    def provider_for_test_3(sender, *args, **kwargs):
        return []

    @provider(provider_test)
    def provider_for_test_4(sender, *args, **kwargs):
        return dict(result4=4)

    results = provider_test.gather()
    assert isinstance(results, GatheredDict)
    assert results["result1"] == 1
    assert "result2" not in results
    assert "result3" not in results
    assert results["result4"] == 4


def test_provider_handle_stop_providing():

    provider_test = Provider()

    @provider(provider_test)
    def provider_for_test(sender, *args, **kwargs):
        return dict(result1=1)

    @provider(provider_test)
    def provider_for_test_2(sender, *args, **kwargs):
        raise StopProviding(result=dict(result2=2))

    @provider(provider_test)
    def provider_for_test_3(sender, *args, **kwargs):
        return dict(result3=3)

    results = provider_test.gather()
    assert isinstance(results, GatheredDict)
    assert results["result1"] == 1
    assert results["result2"] == 2
    assert "result3" not in results


def test_provider_list_results():

    provider_test = Provider(result_class=GatheredList)

    @provider(provider_test)
    def provider_for_test(sender, *args, **kwargs):
        return [1, 2, 3]

    @provider(provider_test)
    def provider_for_test_2(sender, *args, **kwargs):
        return [2, 3, 4]

    results = provider_test.gather()
    assert isinstance(results, GatheredList)
    assert [r for r in results] == [1, 2, 3, 2, 3, 4]

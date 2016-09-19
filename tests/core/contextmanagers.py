# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.dispatch import receiver

from pootle.core.contextmanagers import keep_data, update_data_after
from pootle.core.signals import update_data
from pootle_store.models import Store


@pytest.fixture
def no_update_data_(request):
    receivers = update_data.receivers
    receivers_cache = update_data.sender_receivers_cache.copy()
    update_data.receivers = []

    def _reset_update_data():
        update_data.receivers = receivers
        update_data.sender_receivers_cache = receivers_cache

    request.addfinalizer(_reset_update_data)


@pytest.mark.django_db
def test_contextmanager_keep_data(store0, no_update_data_):

    result = []

    @receiver(update_data, sender=Store)
    def update_data_handler(**kwargs):
        store = kwargs["instance"]
        result.append(store)

    update_data.send(Store, instance=store0)
    assert result == [store0]

    result.remove(store0)

    # with keep_data decorator signal is suppressed
    with keep_data():
        update_data.send(Store, instance=store0)
    assert result == []

    # works again now
    update_data.send(Store, instance=store0)
    assert result == [store0]


@pytest.mark.django_db
def test_contextmanager_keep_data_kwargs(store0, no_update_data_):

    result = []

    @receiver(update_data, sender=Store)
    def update_data_handler(**kwargs):
        result.append(kwargs)

    with update_data_after(store0):
        update_data.send(Store, instance=store0)
        # update_data was not called
        assert result == []
    # update_data called now
    assert len(result) == 1
    assert result[0]["instance"] == store0

    # you can pass args to pass to the update receiver
    result.remove(result[0])
    with update_data_after(store0, foo="apples", bar="oranges"):
        update_data.send(Store, instance=store0)
        assert result == []
    assert len(result) == 1
    assert result[0]["instance"] == store0
    assert result[0]["foo"] == "apples"
    assert result[0]["bar"] == "oranges"

    # you can control the kwargs passed to send inside the context
    result.remove(result[0])
    kwargs = dict(foo="apples", bar="oranges")
    with update_data_after(store0, kwargs=kwargs):
        update_data.send(Store, instance=store0)
        kwargs["foo"] = "plums"
        assert result == []
    assert len(result) == 1
    assert result[0]["instance"] == store0
    assert result[0]["foo"] == "plums"
    assert result[0]["bar"] == "oranges"

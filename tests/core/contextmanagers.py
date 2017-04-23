# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.dispatch import receiver

from pootle.core.contextmanagers import keep_data
from pootle.core.signals import update_data
from pootle_store.models import Store


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

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.signals import update_data


@pytest.fixture
def no_update_data_(request):
    receivers = update_data.receivers
    receivers_cache = update_data.sender_receivers_cache.copy()
    update_data.receivers = []

    def _reset_update_data():
        update_data.receivers = receivers
        update_data.sender_receivers_cache = receivers_cache

    request.addfinalizer(_reset_update_data)

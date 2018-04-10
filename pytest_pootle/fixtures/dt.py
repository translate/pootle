# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import datetime, timedelta

import pytest
import pytz

from pootle.core.utils.timezone import localdate, make_aware


@pytest.fixture
def today():
    return localdate()


@pytest.fixture
def yesterday(today):
    return today - timedelta(days=1)


@pytest.fixture
def dt_today(today):
    return make_aware(
        datetime.combine(
            today,
            datetime.min.time())).astimezone(
                pytz.timezone("UTC"))


@pytest.fixture
def dt_yesterday(yesterday):
    return make_aware(
        datetime.combine(
            yesterday,
            datetime.min.time())).astimezone(
                pytz.timezone("UTC"))

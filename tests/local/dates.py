# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import time
from datetime import datetime

import pytest

from babel.dates import format_timedelta

from pootle.local.dates import localdate, timesince


@pytest.mark.django
def test_local_date_timesince(settings):
    timestamp = time.time() - 1000000
    assert (
        timesince(timestamp)
        == format_timedelta(
            datetime.now()
            - datetime.fromtimestamp(timestamp),
            locale=(
                localdate.locale_code
                or localdate.default_locale)))

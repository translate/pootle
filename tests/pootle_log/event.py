# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import datetime

import pytest

from pootle_log.utils import LogEvent


@pytest.mark.django_db
def test_log_event(store0, member):
    unit = store0.units.first()
    ts = datetime.now()
    log_event = LogEvent(unit, member, ts, "do_foo", "FOO")
    assert log_event.unit == unit
    assert log_event.timestamp == ts
    assert log_event.user == member
    assert log_event.action == "do_foo"
    assert log_event.value == "FOO"
    assert log_event.old_value is None
    assert log_event.revision is None

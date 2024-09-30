# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.contrib.auth import get_user_model

from pootle.core.delegate import log, profile
from pootle_log.formatters import UnitCreatedEvent


@pytest.mark.django_db
def test_log_event_format_unit_created(store0):
    creation_event = list(
        log.get(
            store0.__class__)(store0).get_events(
                event_sources=["unit_source"]))[0]
    formatted_event = UnitCreatedEvent(creation_event)
    assert formatted_event.action == "Unit created"
    assert formatted_event.user == creation_event.user
    user_profile = formatted_event.user_profile
    assert isinstance(user_profile, profile.get(get_user_model()))
    assert user_profile.user == creation_event.user
    assert formatted_event.timestamp == creation_event.timestamp
    assert formatted_event.avatar == user_profile.avatar

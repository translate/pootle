# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import timedelta

import pytest

from django.utils import timezone

from pootle.core.delegate import profile
from pootle.core.utils.templates import render_as_template
from pootle_log.utils import ComparableLogEvent, UserLog
from pootle_profile.utils import UserMembership, UserProfile
from pootle_score.utils import UserScores


@pytest.mark.django_db
def test_profile_user(member):
    user_profile = profile.get(member.__class__)(member)
    assert isinstance(user_profile, UserProfile)
    assert user_profile.user == member
    user_membership = user_profile.membership
    assert isinstance(user_membership, UserMembership)
    assert user_membership.user == member
    user_scores = user_profile.scores
    assert isinstance(user_scores, UserScores)
    assert user_scores.context == member
    assert user_profile.display_name == member.display_name
    avatar = render_as_template(
        "{% load common_tags %}{% avatar username email_hash 20 %}",
        context=dict(
            username=member.username,
            email_hash=member.email_hash))
    assert user_profile.avatar == avatar
    user_log = user_profile.log
    assert isinstance(user_log, UserLog)
    all_events = list(user_profile.get_events())
    assert all(
        (ev.user == member
         or ev.value.user == member)
        for ev in all_events)
    # default is to get events from last 30 days
    thirty_days_ago = timezone.now() - timedelta(days=30)
    assert all(
        (ev.timestamp > thirty_days_ago)
        for ev in all_events)
    events = list(user_profile.get_events(n=2))
    assert all(
        (ev.user == member
         or ev.value.user == member)
        for ev in events)
    assert len(events) == 2
    sorted_events = sorted(ComparableLogEvent(ev) for ev in all_events)
    # last 2 events in the sorted events matches "events"
    assert sorted_events[-1].timestamp == events[0].timestamp
    assert sorted_events[-2].timestamp == events[1].timestamp
    latest_events = list(user_profile.get_events(start=sorted_events[1].timestamp))
    event = latest_events[0]
    no_microseconds = (event.timestamp == event.timestamp.replace(microsecond=0))
    if not no_microseconds:
        assert len(latest_events) == len(all_events) - 1
    assert all(
        (ev.timestamp >= sorted_events[1].timestamp)
        for ev in latest_events)

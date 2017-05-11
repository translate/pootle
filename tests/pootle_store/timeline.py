# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from datetime import timedelta

from django.utils import timezone

from pootle.core.delegate import comparable_event, grouped_events, review
from pootle_store.constants import TRANSLATED, UNTRANSLATED
from pootle_statistics.models import Submission
from pootle_store.models import Suggestion, Unit
from pootle_store.unit.timeline import (
    ACTION_ORDER, ComparableUnitTimelineLogEvent as ComparableLogEvent,
    UnitTimelineGroupedEvents as GroupedEvents, UnitTimelineLog)


def _latest_submission(unit, limit):
    return [
        x for x in unit.submission_set.order_by('-id')[:limit]]


def _get_group_user(group):
    for event in group:
        if event.action == 'suggestion_accepted':
            return event.user
    return group[0].user


def _format_dt(dt, no_microseconds=False):
    if no_microseconds:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    return dt.strftime("%Y-%m-%d %H:%M:%S:%f")


@pytest.mark.django_db
def test_timeline_groups(store0, admin, member, member2, system):
    expected = []

    # 8 - unit_created
    unit = store0.addunit(store0.UnitClass(source="Foo"), user=system)
    unit.refresh_from_db()
    current_time = unit.creation_time.replace(microsecond=0)
    no_microseconds = (unit.creation_time == current_time)
    if no_microseconds:
        Unit.objects.filter(id=unit.id).update(
            creation_time=current_time)
    unit.refresh_from_db()
    expected[:0] = [(set(['unit_created']),
                     _format_dt(unit.creation_time, no_microseconds),
                     system)]

    # 7 - suggestion_created
    suggestion_0, __ = review.get(Suggestion)().add(
        unit,
        "Suggestion for Foo",
        user=member)
    if no_microseconds:
        current_time += timedelta(seconds=1)
        Suggestion.objects.filter(id=suggestion_0.id).update(
            creation_time=current_time)
        suggestion_0.refresh_from_db()
    expected[:0] = [(set(['suggestion_created']),
                     _format_dt(suggestion_0.creation_time, no_microseconds),
                     member)]

    # 6 - suggestion_created
    suggestion_1, __ = review.get(Suggestion)().add(
        unit,
        "Another suggestion for Foo",
        user=member2)
    if no_microseconds:
        current_time += timedelta(seconds=1)
        Suggestion.objects.filter(id=suggestion_1.id).update(
            creation_time=current_time)
        suggestion_1.refresh_from_db()
    expected[:0] = [(set(['suggestion_created']),
                     _format_dt(suggestion_1.creation_time, no_microseconds),
                     member2)]

    # 5 - comment_updated
    unit.translator_comment = "This is a comment!"
    unit.save(user=member)
    submission = _latest_submission(unit, 1)[0]
    if no_microseconds:
        current_time += timedelta(seconds=1)
        Submission.objects.filter(id=submission.id).update(
            creation_time=current_time)
        submission.refresh_from_db()
    unit.refresh_from_db()
    expected[:0] = [(set(['comment_updated']),
                     _format_dt(submission.creation_time, no_microseconds),
                     member)]

    # 4 - suggestion_accepted, target_updated, state_changed
    review.get(Suggestion)([suggestion_0], admin).accept()
    if no_microseconds:
        current_time += timedelta(seconds=1)
        Suggestion.objects.filter(id=suggestion_0.id).update(
            review_time=current_time)
        Submission.objects.filter(suggestion_id=suggestion_0.id).update(
            creation_time=current_time)
        suggestion_0.refresh_from_db()
    unit.refresh_from_db()
    expected[:0] = [(set(['suggestion_accepted', 'target_updated',
                          'state_changed']),
                     _format_dt(suggestion_0.review_time, no_microseconds),
                     admin)]

    # 3 - target_updated
    unit.target = "Overwritten translation for Foo"
    unit.save(user=member2)
    submission = _latest_submission(unit, 1)[0]
    if no_microseconds:
        current_time += timedelta(seconds=1)
        Submission.objects.filter(id=submission.id).update(
            creation_time=current_time)
        submission.refresh_from_db()
    unit.refresh_from_db()
    expected[:0] = [(set(['target_updated']),
                     _format_dt(submission.creation_time, no_microseconds),
                     member2)]

    # 2 - target_updated, state_changed
    unit.target = ""
    unit.save(user=admin)
    submissions = _latest_submission(unit, 2)
    if no_microseconds:
        current_time += timedelta(seconds=1)
        Submission.objects.filter(id__in=[x.id for x in submissions]).update(
            creation_time=current_time)
        for sub in submissions:
            sub.refresh_from_db()
    unit.refresh_from_db()
    expected[:0] = [(set(['target_updated', 'state_changed']),
                     _format_dt(submissions[0].creation_time, no_microseconds),
                     admin)]

    # 1 - suggestion_rejected
    review.get(Suggestion)([suggestion_1], admin).reject()
    if no_microseconds:
        current_time += timedelta(seconds=1)
        Suggestion.objects.filter(id=suggestion_1.id).update(
            review_time=current_time)
        suggestion_1.refresh_from_db()
    expected[:0] = [(set(['suggestion_rejected']),
                     _format_dt(suggestion_1.review_time, no_microseconds),
                     admin)]

    # 0 - comment_updated
    unit.translator_comment = ""
    unit.save(user=admin)
    submission = _latest_submission(unit, 1)[0]
    if no_microseconds:
        current_time += timedelta(seconds=1)
        Submission.objects.filter(id=submission.id).update(
            creation_time=current_time)
        submission.refresh_from_db()
    unit.refresh_from_db()
    expected[:0] = [(set(['comment_updated']),
                     _format_dt(submission.creation_time, no_microseconds),
                     admin)]

    log = UnitTimelineLog(unit)
    grouped_events_class = grouped_events.get(log.__class__)
    assert grouped_events_class == GroupedEvents
    groups = [list(x) for _j, x in grouped_events_class(log).grouped_events()]
    result = [(set([y.action for y in x]),
               _format_dt(x[0].timestamp, no_microseconds),
               _get_group_user(x)) for x in groups]
    assert expected == result


@pytest.mark.django_db
def test_comparable_unit_timelime_log(member, store0):
    assert comparable_event.get(UnitTimelineLog) == ComparableLogEvent

    start = timezone.now().replace(microsecond=0)
    unit = store0.units.filter(state=TRANSLATED).first()
    unit.target += 'UPDATED IN TEST'
    unit.save(user=member)
    unit = store0.units.filter(state=TRANSLATED).first()
    unit.target += 'UPDATED IN TEST AGAIN'
    unit.save(user=member)
    unit_log = UnitTimelineLog(unit)
    event1, event2 = [ComparableLogEvent(x)
                      for x in
                      unit_log.get_events(users=[member.id], start=start)]
    assert (event1 < event2) == (event1.revision < event2.revision)
    assert (event2 < event1) == (event2.revision < event1.revision)

    unit = store0.units.filter(state=UNTRANSLATED).first()
    sugg1, created_ = review.get(Suggestion)().add(
        unit,
        unit.source_f + 'SUGGESTION',
        user=member)
    sugg2, created_ = review.get(Suggestion)().add(
        unit,
        unit.source_f + 'SUGGESTION AGAIN',
        user=member)

    unit_log = UnitTimelineLog(unit)
    Suggestion.objects.filter(id=sugg2.id).update(
        creation_time=sugg1.creation_time + timedelta(seconds=1))
    event1, event2 = [ComparableLogEvent(x)
                      for x in
                      unit_log.get_events(users=[member.id], start=start)]
    assert (event1 < event2) == (event1.timestamp < event2.timestamp)
    assert (event2 < event1) == (event2.timestamp < event1.timestamp)

    Suggestion.objects.filter(id=sugg2.id).update(
        creation_time=sugg1.creation_time)
    event1, event2 = [ComparableLogEvent(x)
                      for x in
                      unit_log.get_events(users=[member.id], start=start)]
    assert (event1 < event2) == (event1.value.pk < event2.value.pk)
    assert (event2 < event1) == (event2.value.pk < event1.value.pk)

    Suggestion.objects.filter(id=sugg2.id).update(creation_time=None)
    sugg2 = Suggestion.objects.get(id=sugg2.id)
    event1 = [ComparableLogEvent(x)
              for x in
              unit_log.get_events(users=[member.id], start=start)][0]
    event2 = ComparableLogEvent(unit_log.event(sugg2.unit,
                                               sugg2.user,
                                               sugg2.creation_time,
                                               "suggestion_created",
                                               sugg2))
    assert event2 < event1
    assert not (event1 < event2)

    unit = store0.units.filter(state=UNTRANSLATED)[0]
    unit.target = 'Unit Target'
    unit.save()
    unit_log = UnitTimelineLog(unit)
    event1, event2 = [ComparableLogEvent(x)
                      for x in unit_log.get_submission_events()]
    assert (event1 < event2) == (
        ACTION_ORDER[event1.action] < ACTION_ORDER[event2.action])
    assert (event2 < event1) == (
        ACTION_ORDER[event2.action] < ACTION_ORDER[event1.action])

    assert not (event1 < event1) and not (event1 > event1)

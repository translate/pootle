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

from pootle.core.delegate import comparable_event, review
from pootle_store.constants import TRANSLATED, UNTRANSLATED
from pootle_store.models import Suggestion
from pootle_store.unit.timeline import (
    ACTION_ORDER, ComparableUnitTimelineLogEvent as ComparableLogEvent,
    UnitTimelineLog)


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

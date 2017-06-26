# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from datetime import timedelta

from translate.filters.decorators import Category

from django.urls import reverse
from django.utils import timezone
from django.utils.html import format_html

from accounts.proxy import DisplayUser

from pootle.core.delegate import comparable_event, grouped_events, review
from pootle_checks.constants import CHECK_NAMES
from pootle_comment.forms import UnsecuredCommentForm
from pootle_store.constants import (
    FUZZY, STATES_MAP, TRANSLATED, UNTRANSLATED)
from pootle_statistics.models import Submission, SubmissionFields
from pootle_store.fields import to_python
from pootle_store.models import QualityCheck, Suggestion, Unit
from pootle_store.unit.timeline import (
    ACTION_ORDER, ComparableUnitTimelineLogEvent as ComparableLogEvent,
    UnitTimelineGroupedEvents as GroupedEvents, Timeline, UnitTimelineLog)


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


@pytest.mark.django_db
def test_timeline_translated_unit_creation(store0, member):
    pounit = store0.UnitClass(source="Foo")
    pounit.target = "Bar"
    unit = store0.addunit(pounit, user=member)
    unit.refresh_from_db()
    groups = Timeline(unit).grouped_events()
    assert len(groups) == 1
    group = groups[0]
    assert len(group['events']) == 1
    assert group['events'][0]['value'] == unit.target
    assert group['events'][0]['translation']
    assert group['events'][0]['description'] == u"Unit created"
    assert group['via_upload'] is False
    assert group['datetime'] == unit.creation_time
    assert group['user'].username == member.username


@pytest.mark.django_db
def test_timeline_untranslated_unit_creation(store0, member):
    unit = store0.addunit(store0.UnitClass(source="Foo"), user=member)
    unit.refresh_from_db()
    groups = Timeline(unit).grouped_events()
    assert len(groups) == 1
    group = groups[0]
    assert len(group['events']) == 1
    assert 'value' not in group['events'][0]
    assert 'translation' not in group['events'][0]
    assert group['events'][0]['description'] == u"Unit created"
    assert group['via_upload'] is False
    assert group['datetime'] == unit.creation_time
    assert group['user'].username == member.username


@pytest.mark.django_db
def test_timeline_untranslated_unit_creation_with_updates(store0, member):
    unit = store0.addunit(store0.UnitClass(source="Foo"), user=member)
    unit.refresh_from_db()
    unit.target = 'Bar'
    unit.save()
    unit.refresh_from_db()
    groups = Timeline(unit).grouped_events()
    assert len(groups) == 2
    group = groups[-1]
    assert len(group['events']) == 1
    assert 'value' not in group['events'][0]
    assert 'translation' not in group['events'][0]
    assert group['events'][0]['description'] == u"Unit created"
    assert group['via_upload'] is False
    assert group['datetime'] == unit.creation_time
    assert group['user'].username == member.username


@pytest.mark.django_db
def test_timeline_translated_unit_creation_with_updates(store0, member):
    pounit = store0.UnitClass(source="Foo")
    pounit.target = "Bar"
    unit = store0.addunit(pounit, user=member)
    unit.refresh_from_db()
    unit.target = "Bar UPDATED"
    unit.save()
    unit.refresh_from_db()
    groups = Timeline(unit).grouped_events()
    assert len(groups) == 2
    group = groups[-1]
    assert len(group['events']) == 1
    assert group['events'][0]['value'] == "Bar"
    assert group['events'][0]['translation']
    assert group['events'][0]['description'] == u"Unit created"
    assert group['via_upload'] is False
    assert group['datetime'] == unit.creation_time
    assert group['user'].username == member.username


def _get_sugg_accepted_desc(suggestion):
    user = DisplayUser(suggestion.user.username, suggestion.user.full_name)
    params = {'author': user.author_link}
    return u'Accepted suggestion from %(author)s' % params


def _get_sugg_accepted_with_comment_desc(suggestion, comment):
    user = DisplayUser(suggestion.user.username, suggestion.user.full_name)
    params = {
        'author': user.author_link,
        'comment': format_html(u'<span class="comment">{}</span>',
                               comment)}

    return (u'Accepted suggestion from %(author)s '
            u'with comment: %(comment)s' % params)


def _get_state_changed_value(submission):
    params = {
        'old_value': STATES_MAP[int(to_python(submission.old_value))],
        'new_value': STATES_MAP[int(to_python(submission.new_value))]}
    return (
        u"%(old_value)s "
        u"<span class='timeline-arrow'></span> "
        u"%(new_value)s" % params)


def _get_update_check_desc(submission):
    check_name = submission.quality_check.name
    check_url = u''.join(
        [reverse('pootle-checks-descriptions'),
         '#', check_name])
    check_link = format_html("<a href='{}'>{}</a>", check_url,
                             CHECK_NAMES[check_name])

    action = ''
    if submission.old_value == '1' and submission.new_value == '0':
        action = 'Muted'
    if submission.old_value == '0' and submission.new_value == '1':
        action = 'Unmuted'

    return ("%(action)s %(check_link)s check" %
            {'check_link': check_link, 'action': action})


@pytest.mark.django_db
def test_timeline_translated_unit_with_suggestion(store0, admin):
    suggestion = Suggestion.objects.filter(
        unit__store=store0,
        state__name="pending",
        unit__state=TRANSLATED).first()
    unit = suggestion.unit
    review.get(Suggestion)([suggestion], admin).accept()
    suggestion.refresh_from_db()
    unit.refresh_from_db()
    timeline = Timeline(unit)
    groups = timeline.grouped_events(start=suggestion.review_time)
    assert len(groups) == 1
    group = groups[0]
    assert len(group['events']) == 1
    assert group['events'][0]['value'] == unit.target
    assert group['events'][0]['translation']
    assert (group['events'][0]['description'] ==
            _get_sugg_accepted_desc(suggestion))

    assert group['via_upload'] is False
    assert group['datetime'] == suggestion.review_time
    assert group['user'].username == admin.username


@pytest.mark.django_db
def test_timeline_unit_with_suggestion_and_comment(store0, admin):
    suggestion = Suggestion.objects.filter(
        unit__store=store0,
        state__name="pending",
        unit__state=UNTRANSLATED).first()
    unit = suggestion.unit
    review.get(Suggestion)([suggestion], admin).accept()
    comment = 'This is a comment!'
    form = UnsecuredCommentForm(suggestion, admin, dict(
        comment=comment))

    assert form.is_valid()
    form.save()

    suggestion.refresh_from_db()
    unit.refresh_from_db()
    timeline = Timeline(unit)
    groups = timeline.grouped_events(start=suggestion.review_time)
    assert len(groups) == 1
    group = groups[0]
    assert len(group['events']) == 2
    assert group['events'][0]['value'] == unit.target
    assert group['events'][0]['translation']
    assert (group['events'][0]['description'] ==
            _get_sugg_accepted_with_comment_desc(suggestion, comment))

    submission = Submission.objects.get(field=SubmissionFields.STATE,
                                        unit=suggestion.unit,
                                        creation_time=suggestion.review_time)
    assert group['events'][1]['value'] == _get_state_changed_value(submission)
    assert group['via_upload'] is False
    assert group['datetime'] == suggestion.review_time
    assert group['user'].username == admin.username


@pytest.mark.django_db
def test_timeline_unfuzzied_unit(member):
    unit = Unit.objects.filter(state=FUZZY).first()
    unit.markfuzzy(False)
    unit.save(user=member)
    last_submission = unit.store.data.last_submission
    groups = Timeline(unit).grouped_events(
        start=last_submission.creation_time)
    assert len(groups) == 1
    group = groups[0]
    assert len(group['events']) == 1
    assert (group['events'][0]['value'] ==
            _get_state_changed_value(last_submission))
    assert group['events'][0]['state']
    assert 'description' not in group['events'][0]
    assert group['via_upload'] is False
    assert group['datetime'] == last_submission.creation_time
    assert group['user'].username == member.username


@pytest.mark.django_db
def test_timeline_unit_with_qc(store0, admin, member):
    qc_filter = dict(
        unit__store=store0,
        unit__state=TRANSLATED,
        unit__store__translation_project__project__disabled=False,
        unit__store__obsolete=False,
        category=Category.CRITICAL)
    qc = QualityCheck.objects.filter(**qc_filter).first()
    unit = qc.unit
    unit.toggle_qualitycheck(qc.id, True, member)
    last_submission_0 = unit.store.data.last_submission
    unit.toggle_qualitycheck(qc.id, False, admin)
    unit.store.data.refresh_from_db()
    last_submission_1 = unit.store.data.last_submission
    groups = Timeline(unit).grouped_events(
        start=last_submission_0.creation_time)
    assert len(groups) == 2
    group = groups[1]
    assert len(group['events']) == 1
    assert 'value' not in group['events'][0]
    assert (group['events'][0]['description'] ==
            _get_update_check_desc(last_submission_0))
    assert group['via_upload'] is False
    assert group['user'].username == member.username
    assert group['datetime'] == last_submission_0.creation_time

    group = groups[0]
    assert len(group['events']) == 1
    assert 'value' not in group['events'][0]
    assert (group['events'][0]['description'] ==
            _get_update_check_desc(last_submission_1))
    assert group['via_upload'] is False
    assert group['user'].username == admin.username
    assert group['datetime'] == last_submission_1.creation_time


@pytest.mark.django_db
def test_timeline_translated_unit_comment(store0, admin, member):
    unit = store0.units.filter(state=TRANSLATED).first()
    comment = 'This is a comment!'
    unit.translator_comment = comment
    unit.save(user=member)
    last_submission_0 = unit.store.data.last_submission
    unit.translator_comment = ''
    unit.save(user=admin)
    unit.store.data.refresh_from_db()
    last_submission_1 = unit.store.data.last_submission
    groups = Timeline(unit).grouped_events(
        start=last_submission_0.creation_time)
    assert len(groups) == 2
    group = groups[1]
    assert len(group['events']) == 1
    assert group['events'][0]['value'] == comment
    assert group['events'][0]['comment']
    assert 'description' not in group['events'][0]
    assert group['via_upload'] is False
    assert group['datetime'] == last_submission_0.creation_time
    assert group['user'].username == member.username

    group = groups[0]
    assert len(group['events']) == 1
    assert 'value' not in group['events'][0]
    assert 'comment' not in group['events'][0]
    assert group['events'][0]['description'] == 'Removed comment'
    assert group['via_upload'] is False
    assert group['datetime'] == last_submission_1.creation_time
    assert group['user'].username == admin.username

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import lifecycle, review
from pootle_log.utils import Log, LogEvent
from pootle_statistics.models import (
    Submission, SubmissionFields, SubmissionTypes)
from pootle_store.models import Suggestion, UnitSource


def _get_mid_times(qs, field="creation_time"):
    qs_start = qs.order_by(
        field).values_list(
            field, flat=True).first()
    qs_end = qs.order_by(
        field).values_list(
            field, flat=True).last()
    qs_delta = (qs_end - qs_start) / 3
    qs_start += qs_delta
    qs_end -= qs_delta
    return qs_start, qs_end


def test_log_base():
    base_log = Log()
    assert base_log.event == LogEvent
    assert (
        base_log.subtypes
        == {getattr(SubmissionTypes, n): n.lower()
            for n in ["WEB", "UPLOAD", "SYSTEM"]})
    assert (
        base_log.subfields
        == {getattr(SubmissionFields, n): n.lower()
            for n
            in ["SOURCE", "TARGET", "STATE", "COMMENT", "CHECK"]})


@pytest.mark.django_db
def test_log_filter_store(store0):
    subs = Submission.objects.all()
    suggestions = Suggestion.objects.all()
    unit_sources = UnitSource.objects.all()
    for qs in [subs, suggestions, unit_sources]:
        assert (
            list(
                Log().filter_store(
                    qs,
                    store0.pk))
            == list(qs.filter(unit__store=store0)))
        # None should return original qs
        assert (
            Log().filter_store(qs, None)
            == qs)


@pytest.mark.django_db
def test_log_filter_path(tp0, store0):
    subs = Submission.objects.all()
    suggestions = Suggestion.objects.all()
    unit_sources = UnitSource.objects.all()
    for path in [tp0.pootle_path, store0.pootle_path]:
        for qs in [subs, suggestions, unit_sources]:
            assert (
                list(Log().filter_path(qs, path))
                == list(
                    qs.filter(
                        unit__store__pootle_path__startswith=path)))
            # None should return original qs
            assert Log().filter_path(qs, None) == qs


@pytest.mark.django_db
def test_log_filter_user(member):
    subs = Submission.objects.all()
    suggestions = Suggestion.objects.all()
    unit_sources = UnitSource.objects.all()
    assert (
        list(Log().filter_user(subs, member.id))
        == list(
            subs.filter(submitter=member)))
    assert (
        list(Log().filter_user(suggestions, member.id, field="user_id"))
        == list(
            suggestions.filter(user=member)))
    assert (
        list(Log().filter_user(suggestions, member.id, field="reviewer_id"))
        == list(
            suggestions.filter(reviewer=member)))
    assert (
        list(Log().filter_user(unit_sources, member.id, field="created_by_id"))
        == list(
            unit_sources.filter(created_by=member)))
    for qs in [subs, suggestions, unit_sources]:
        # None should return original qs
        assert Log().filter_user(qs, None) == qs


@pytest.mark.django_db
def test_log_filter_sub_timestamps(member):
    subs = Submission.objects.all()
    sub_start, sub_end = _get_mid_times(subs)
    assert (
        list(Log().filter_timestamps(subs, start=sub_start))
        == list(
            subs.filter(creation_time__gte=sub_start)))
    assert (
        list(Log().filter_timestamps(subs, end=sub_end))
        == list(
            subs.filter(creation_time__lt=sub_end)))
    assert (
        list(Log().filter_timestamps(
            subs, start=sub_start, end=sub_end))
        == list(
            subs.filter(
                creation_time__lt=sub_end).filter(
                    creation_time__gte=sub_start)))
    # None should return original qs
    assert Log().filter_timestamps(subs, start=None, end=None) == subs


@pytest.mark.django_db
def test_log_filter_sugg_timestamps(member):
    suggs = Suggestion.objects.all()
    sugg_start, sugg_end = _get_mid_times(suggs)
    assert (
        list(Log().filter_timestamps(suggs, start=sugg_start))
        == list(
            suggs.filter(creation_time__gte=sugg_start)))
    assert (
        list(Log().filter_timestamps(suggs, end=sugg_end))
        == list(
            suggs.filter(creation_time__lt=sugg_end)))
    assert (
        list(Log().filter_timestamps(suggs, start=sugg_start, end=sugg_end))
        == list(
            suggs.filter(
                creation_time__lt=sugg_end).filter(
                    creation_time__gte=sugg_start)))
    # None should return original qs
    assert Log().filter_timestamps(suggs, start=None, end=None) == suggs


@pytest.mark.django_db
def test_log_filter_unit_create_timestamps(member):
    unit_creates = UnitSource.objects.all()
    unit_create_start, unit_create_end = _get_mid_times(
        unit_creates, field="unit__creation_time")
    assert (
        list(Log().filter_timestamps(
            unit_creates,
            start=unit_create_start,
            field="unit__creation_time"))
        == list(
            unit_creates.filter(
                unit__creation_time__gte=unit_create_start)))
    assert (
        list(Log().filter_timestamps(
            unit_creates,
            end=unit_create_end,
            field="unit__creation_time"))
        == list(
            unit_creates.filter(
                unit__creation_time__lt=unit_create_end)))
    assert (
        list(Log().filter_timestamps(
            unit_creates,
            start=unit_create_start,
            end=unit_create_end,
            field="unit__creation_time"))
        == list(
            unit_creates.filter(
                unit__creation_time__lt=unit_create_end).filter(
                    unit__creation_time__gte=unit_create_start)))
    # None should return original qs
    assert (
        Log().filter_timestamps(
            unit_creates,
            start=None,
            end=None,
            field="unit__creation_time")
        == unit_creates)


@pytest.mark.django_db
def test_log_filtered_suggestions(member, tp0, store0):
    suggs = Suggestion.objects.all()
    sugg_start, sugg_end = _get_mid_times(suggs)
    sugg_log = Log()
    # no filtering
    assert (
        sugg_log.filtered_suggestions().count()
        == sugg_log.suggestions.count()
        == suggs.count())
    user_suggestions = (
        sugg_log.filter_user(
            sugg_log.suggestions,
            member,
            field="user_id")
        | sugg_log.filter_user(
            sugg_log.suggestions,
            member,
            field="reviewer_id"))
    assert user_suggestions
    assert (
        list(user_suggestions.order_by("id"))
        == list(sugg_log.filtered_suggestions(
            user=member).order_by("id")))
    time_suggestions = (
        sugg_log.filter_timestamps(
            sugg_log.suggestions,
            start=sugg_start,
            end=sugg_end)
        | sugg_log.filter_timestamps(
            sugg_log.suggestions,
            start=sugg_start,
            end=sugg_end,
            field="review_time"))
    assert time_suggestions
    assert (
        list(time_suggestions.order_by("id"))
        == list(sugg_log.filtered_suggestions(
            start=sugg_start, end=sugg_end).order_by("id")))
    user_time_suggestions = (
        (sugg_log.filter_user(
            sugg_log.suggestions,
            member,
            field="user_id")
         & sugg_log.filter_timestamps(
             sugg_log.suggestions,
             start=sugg_start,
             end=sugg_end))
        | (sugg_log.filter_user(
            sugg_log.suggestions,
            member,
            field="reviewer_id")
           & sugg_log.filter_timestamps(
               sugg_log.suggestions,
               start=sugg_start,
               end=sugg_end,
               field="review_time")))
    assert user_time_suggestions
    assert (
        list(user_time_suggestions.order_by("id"))
        == list(sugg_log.filtered_suggestions(
            start=sugg_start, end=sugg_end, user=member).order_by("id")))
    store_suggestions = sugg_log.filter_store(
        sugg_log.suggestions, store0.pk)
    assert store_suggestions
    assert (
        list(store_suggestions.order_by("id"))
        == list(sugg_log.filtered_suggestions(
            store=store0.id).order_by("id")))
    path_suggestions = sugg_log.filter_path(
        sugg_log.suggestions, tp0.pootle_path)
    assert path_suggestions.count()
    assert (
        path_suggestions.count()
        == sugg_log.filtered_suggestions(path=tp0.pootle_path).count())


@pytest.mark.django_db
def test_log_filtered_submissions(member, tp0, store0):
    subs = Submission.objects.all()
    sub_start, sub_end = _get_mid_times(subs)
    sub_log = Log()
    # no filtering
    assert (
        sub_log.filtered_submissions().count()
        == sub_log.submissions.count()
        == subs.count())
    user_subs = (
        sub_log.filter_user(
            sub_log.submissions,
            member))
    assert user_subs.count()
    assert (
        list(user_subs)
        == list(sub_log.filtered_submissions(user=member)))
    time_subs = (
        sub_log.filter_timestamps(
            sub_log.submissions,
            start=sub_start,
            end=sub_end))
    assert time_subs.count()
    assert (
        list(time_subs)
        == list(sub_log.filtered_submissions(
            start=sub_start, end=sub_end)))
    store_subs = (
        sub_log.filter_store(
            sub_log.submissions,
            store0.pk))
    assert store_subs.count()
    assert (
        list(sub_log.submissions.filter(unit__store_id=store0.pk))
        == list(store_subs))
    path_subs = (
        sub_log.filter_path(
            sub_log.submissions,
            tp0.pootle_path))
    assert path_subs.count()
    assert (
        sub_log.submissions.filter(
            unit__store__pootle_path__startswith=tp0.pootle_path).count()
        == path_subs.count())


@pytest.mark.django_db
def test_log_filtered_created_units(system, tp0, store0):
    created_units = UnitSource.objects.all()
    created_unit_start, created_unit_end = _get_mid_times(
        created_units, field="unit__creation_time")
    created_unit_log = Log()
    # no filtering
    assert (
        created_unit_log.filtered_created_units().count()
        == created_unit_log.created_units.count()
        == created_units.count())
    user_created_units = created_unit_log.filter_user(
        created_unit_log.created_units,
        system.id,
        field="created_by_id")
    assert user_created_units.count()
    assert (
        list(user_created_units)
        == list(created_unit_log.filtered_created_units(user=system)))
    # using start and end seems to create empty - so only testing start
    time_created_units = created_unit_log.filter_timestamps(
        created_unit_log.created_units,
        start=created_unit_start,
        field="unit__creation_time")
    assert time_created_units.count()
    assert (
        list(time_created_units)
        == list(created_unit_log.filtered_created_units(
            start=created_unit_start)))
    store_created_units = created_unit_log.filter_store(
        created_unit_log.created_units,
        store0.pk)
    assert store_created_units.count()
    assert (
        list(created_unit_log.filtered_created_units(store=store0.pk))
        == list(store_created_units))
    path_created_units = created_unit_log.filter_path(
        created_unit_log.created_units,
        tp0.pootle_path)
    assert path_created_units.count()
    assert (
        created_unit_log.filtered_created_units(path=tp0.pootle_path).count()
        == path_created_units.count())


@pytest.mark.django_db
def test_log_get_created_units(system, store0):
    created_units = UnitSource.objects.all()
    created_unit_log = Log()
    created = created_unit_log.get_created_units()
    assert type(created).__name__ == "generator"
    assert len(list(created)) == created_units.count()
    expected = created_units.filter(
        created_by=system).filter(
            unit__store=store0).in_bulk()
    result = created_unit_log.get_created_units(
        store=store0.pk, user=system)
    for event in result:
        created_unit = expected[event.value.pk]
        assert isinstance(event, created_unit_log.event)
        assert event.unit == created_unit.unit
        assert event.user == created_unit.created_by
        assert event.timestamp == created_unit.unit.creation_time
        assert event.action == "unit_created"
        assert event.value == created_unit


@pytest.mark.django_db
def test_log_get_submissions(member, store0):
    submissions = Submission.objects.all()
    submission_log = Log()
    sub_events = submission_log.get_submissions()
    unit0 = store0.units[0]
    unit0.source = "new source"
    unit0.save(submitted_by=member)
    lifecycle.get(unit0.__class__)(unit0).change()
    unit1 = store0.units[0]
    unit1.translator_comment = "new comment"
    unit1.save(commented_by=member)
    lifecycle.get(unit1.__class__)(unit1).change()
    qc = store0.units.filter(
        qualitycheck__isnull=False)[0].qualitycheck_set.all()[0]
    lifecycle.get(qc.unit.__class__)(qc.unit).sub_mute_qc(
        submitter=member, quality_check=qc).save()
    assert type(sub_events).__name__ == "generator"
    assert len(list(sub_events)) == submissions.count()
    expected = submissions.filter(
        submitter=member).filter(
            unit__store=store0).in_bulk()
    result = submission_log.get_submissions(
        store=store0.pk, user=member)
    for event in result:
        sub = expected[event.value.pk]
        event_name = "state_changed"
        if sub.field == SubmissionFields.CHECK:
            event_name = (
                "check_muted"
                if sub.new_value == "0"
                else "check_unmuted")
        elif sub.field == SubmissionFields.TARGET:
            event_name = "target_updated"
        elif sub.field == SubmissionFields.SOURCE:
            event_name = "source_updated"
        elif sub.field == SubmissionFields.COMMENT:
            event_name = "comment_updated"
        assert isinstance(event, submission_log.event)
        assert event.unit == sub.unit
        assert event.user == sub.submitter
        assert event.timestamp == sub.creation_time
        assert event.action == event_name
        assert event.value == sub


@pytest.mark.django_db
def test_log_get_suggestions(member, store0):
    suggestions = Suggestion.objects.all()
    sugg_start, sugg_end = _get_mid_times(suggestions)
    sugg_log = Log()
    sugg_events = sugg_log.get_suggestions()
    assert type(sugg_events).__name__ == "generator"
    user_time_suggestions = (
        (sugg_log.filter_user(
            sugg_log.suggestions,
            member,
            field="user_id")
         & sugg_log.filter_timestamps(
             sugg_log.suggestions,
             start=sugg_start,
             end=sugg_end))
        | (sugg_log.filter_user(
            sugg_log.suggestions,
            member,
            field="reviewer_id")
           & sugg_log.filter_timestamps(
               sugg_log.suggestions,
               start=sugg_start,
               end=sugg_end,
               field="review_time")))
    assert user_time_suggestions
    pending = suggestions.filter(
        creation_time__gte=sugg_start,
        creation_time__lt=sugg_end,
        state__name="pending").first()
    review.get(Suggestion)([pending], member).accept()
    pending = suggestions.filter(
        creation_time__gte=sugg_start,
        creation_time__lt=sugg_end,
        state__name="pending").first()
    review.get(Suggestion)([pending], member).reject()
    pending.review_time = sugg_start
    pending.save()
    expected = {}
    for suggestion in user_time_suggestions.all():
        add_event = (
            (suggestion.creation_time >= sugg_start)
            and (suggestion.creation_time < sugg_end)
            and (suggestion.user == member))
        review_event = (
            (suggestion.review_time >= sugg_start)
            and (suggestion.review_time < sugg_end)
            and (suggestion.reviewer == member))
        expected[suggestion.id] = {}
        if add_event:
            expected[suggestion.id]["suggestion_created"] = (
                sugg_log.event(
                    suggestion.unit,
                    suggestion.user,
                    suggestion.creation_time,
                    "suggestion_created",
                    suggestion))
        if review_event:
            event_name = (
                "suggestion_accepted"
                if suggestion.state.name == "accepted"
                else "suggestion_rejected")
            expected[suggestion.id][event_name] = (
                sugg_log.event(
                    suggestion.unit,
                    suggestion.reviewer,
                    suggestion.review_time,
                    event_name,
                    suggestion))
    result = sugg_log.get_suggestions(
        start=sugg_start, end=sugg_end, user=member)
    for event in result:
        assert isinstance(event, sugg_log.event)
        sugg_review = expected[event.value.pk][event.action]
        assert event.unit == sugg_review.unit
        assert event.action in [
            "suggestion_created", "suggestion_accepted", "suggestion_rejected"]
        assert event.user == (
            sugg_review.value.user
            if event.action == "suggestion_created"
            else sugg_review.value.reviewer)
        assert event.timestamp == (
            sugg_review.value.creation_time
            if event.action == "suggestion_created"
            else sugg_review.value.review_time)
        assert event.value == sugg_review.value


@pytest.mark.django_db
def test_log_get_events(site_users, store0):
    user = site_users["user"]
    event_log = Log()
    kwargs = dict(user=user, store=store0)
    result = sorted(
        event_log.get_events(**kwargs),
        key=(lambda ev: (ev.timestamp, ev.unit.pk)))
    expected = sorted(
        list(event_log.get_created_units(**kwargs))
        + list(event_log.get_suggestions(**kwargs))
        + list(event_log.get_submissions(**kwargs)),
        key=(lambda ev: (ev.timestamp, ev.unit.pk)))
    assert (
        [(x.timestamp, x.unit, x.action)
         for x in result]
        == [(x.timestamp, x.unit, x.action)
            for x in expected])

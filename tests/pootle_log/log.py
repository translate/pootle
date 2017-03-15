# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

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

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import datetime

import pytest

from django.utils import timezone

from pootle.core.delegate import event_score
from pootle.core.utils.timezone import make_aware
from pootle_log.utils import LogEvent
from pootle_score import scores
from pootle_statistics.models import Submission
from pootle_store.constants import FUZZY, TRANSLATED, UNTRANSLATED


@pytest.mark.django_db
def test_score_event_suggestion_created(store0, admin, settings):
    unit = store0.units.filter(suggestion__state__name="pending").first()
    suggestion = unit.suggestion_set.filter(state__name="pending").first()
    scoring = event_score.gather(LogEvent)
    scorer = scoring["suggestion_created"]
    assert scorer == scores.SuggestionCreatedScore
    event = LogEvent(
        unit, admin, datetime.now(), "example", suggestion)
    score = scorer(event)
    assert score.event == event
    assert score.unit == unit
    assert score.suggestion == suggestion
    assert (
        score.score
        == (unit.unit_source.source_wordcount
            * settings.POOTLE_SCORES["suggestion_add"]))
    assert score.translated == 0
    assert score.reviewed == 0
    assert score.suggested == unit.unit_source.source_wordcount


@pytest.mark.django_db
def test_score_event_suggestion_accepted(store0, admin, settings):
    unit = store0.units.filter(suggestion__state__name="pending").first()
    suggestion = unit.suggestion_set.filter(state__name="pending").first()
    scoring = event_score.gather(LogEvent)
    scorer = scoring["suggestion_accepted"]
    assert scorer == scores.SuggestionAcceptedScore
    event = LogEvent(
        unit, admin, datetime.now(), "example", suggestion)
    score = scorer(event)
    assert score.event == event
    assert score.unit == unit
    assert score.suggestion == suggestion
    assert (
        score.score
        == (unit.unit_source.source_wordcount
            * settings.POOTLE_SCORES["suggestion_accept"]))
    assert score.translated == 0
    assert score.reviewed == unit.unit_source.source_wordcount
    assert score.suggested == 0
    assert (
        score.get_score()
        == dict(
            score=score.score,
            translated=0,
            reviewed=unit.unit_source.source_wordcount,
            suggested=0))


@pytest.mark.django_db
def test_score_event_suggestion_rejected(store0, admin, settings):
    unit = store0.units.filter(suggestion__state__name="pending").first()
    suggestion = unit.suggestion_set.filter(state__name="pending").first()
    scoring = event_score.gather(LogEvent)
    scorer = scoring["suggestion_rejected"]
    assert scorer == scores.SuggestionRejectedScore
    event = LogEvent(
        unit, admin, datetime.now(), "example", suggestion)
    score = scorer(event)
    assert score.event == event
    assert score.unit == unit
    assert score.suggestion == suggestion
    assert (
        score.score
        == (unit.unit_source.source_wordcount
            * settings.POOTLE_SCORES["suggestion_reject"]))
    assert score.translated == 0
    assert score.reviewed == unit.unit_source.source_wordcount
    assert score.suggested == 0
    assert (
        score.get_score()
        == dict(
            score=score.score,
            translated=0,
            reviewed=unit.unit_source.source_wordcount,
            suggested=0))


@pytest.mark.django_db
def test_score_event_target_updated(store0, admin, settings):
    unit = store0.units.first()
    scoring = event_score.gather(LogEvent)
    scorer = scoring["target_updated"]
    assert scorer == scores.TargetUpdatedScore
    event = LogEvent(
        unit, admin, datetime.now(), "example", None)
    score = scorer(event)
    assert score.event == event
    assert score.unit == unit
    assert (
        score.score
        == (unit.unit_source.source_wordcount
            * settings.POOTLE_SCORES["target_updated"]))
    assert score.translated == unit.unit_source.source_wordcount
    assert score.reviewed == 0
    assert score.suggested == 0
    assert (
        score.get_score()
        == dict(
            score=score.score,
            translated=unit.unit_source.source_wordcount,
            reviewed=0,
            suggested=0))


@pytest.mark.django_db
def test_score_event_state_updated(store0, admin, settings):
    unit = store0.units.first()
    scoring = event_score.gather(LogEvent)
    scorer = scoring["state_updated"]
    assert scorer == scores.StateUpdatedScore
    sub = Submission.objects.create(
        unit=unit,
        submitter=admin,
        translation_project=unit.store.translation_project,
        creation_time=make_aware(timezone.now()),
        old_value=UNTRANSLATED,
        new_value=TRANSLATED)
    event = LogEvent(
        unit, admin, datetime.now(), "example", sub)
    score = scorer(event)
    assert score.event == event
    assert score.unit == unit
    assert score.submission == sub
    assert (
        score.score
        == (unit.unit_source.source_wordcount
            * settings.POOTLE_SCORES["state_translated"]))
    assert score.translated == unit.unit_source.source_wordcount
    assert score.reviewed == 0
    assert score.suggested == 0
    assert (
        score.get_score()
        == dict(
            score=score.score,
            translated=unit.unit_source.source_wordcount,
            reviewed=0,
            suggested=0))
    sub = Submission.objects.create(
        unit=unit,
        submitter=admin,
        translation_project=unit.store.translation_project,
        creation_time=make_aware(timezone.now()),
        old_value=FUZZY,
        new_value=TRANSLATED)
    event = LogEvent(
        unit, admin, datetime.now(), "example", sub)
    score = scorer(event)
    assert score.event == event
    assert score.unit == unit
    assert score.submission == sub
    assert (
        score.score
        == (unit.unit_source.source_wordcount
            * settings.POOTLE_SCORES["state_unfuzzy"]))
    assert score.translated == 0
    assert score.reviewed == unit.unit_source.source_wordcount
    assert score.suggested == 0
    assert (
        score.get_score()
        == dict(
            score=score.score,
            translated=0,
            reviewed=unit.unit_source.source_wordcount,
            suggested=0))
    sub = Submission.objects.create(
        unit=unit,
        submitter=admin,
        translation_project=unit.store.translation_project,
        creation_time=make_aware(timezone.now()),
        old_value=TRANSLATED,
        new_value=FUZZY)
    event = LogEvent(
        unit, admin, datetime.now(), "example", sub)
    score = scorer(event)
    assert score.event == event
    assert score.unit == unit
    assert score.submission == sub
    assert (
        score.score
        == (unit.unit_source.source_wordcount
            * settings.POOTLE_SCORES["state_fuzzy"]))
    assert score.translated == 0
    assert score.reviewed == unit.unit_source.source_wordcount
    assert score.suggested == 0
    assert (
        score.get_score()
        == dict(
            score=score.score,
            translated=0,
            reviewed=unit.unit_source.source_wordcount,
            suggested=0))

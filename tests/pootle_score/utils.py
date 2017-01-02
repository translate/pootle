# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import timedelta

import pytest

from django.db.models import Sum
from django.utils import timezone

from pootle.core.delegate import revision, scores
from pootle_score.apps import PootleScoreConfig
from pootle_score.models import UserTPScore
from pootle_score.utils import (
    LanguageScores, ProjectScores, ProjectSetScores, TPScores)


def _test_scores(ns, context, score_data):
    today = timezone.now().date()
    assert score_data.context == context
    assert (
        score_data.get_daterange(30)
        == (today - timedelta(days=30), today))
    assert score_data.ns == "pootle.score.%s" % ns
    assert score_data.sw_version == PootleScoreConfig.version
    assert score_data.score_model == UserTPScore.objects
    assert (
        list(score_data.scores_within_days(5))
        == list(score_data.score_model.filter(
            date__range=score_data.get_daterange(5))))
    assert (
        list(score_data.get_scores(5))
        == list(score_data.filter_scores(score_data.scores_within_days(5))))
    assert (
        list(score_data.get_top_scorers(10))
        == list(
            score_data.get_scores(10).order_by("user__username").values(
                "user__username", "user__email", "user__full_name").annotate(
                    Sum("score"),
                    Sum("suggested"),
                    Sum("reviewed"),
                    Sum("translated")).order_by("-score__sum")))
    assert (
        tuple(score_data.top_scorers)
        == tuple(score_data.get_top_scorers(30)))
    assert (
        score_data.revision
        == revision.get(context.directory.__class__)(
            context.directory).get(key="stats"))


@pytest.mark.django_db
def test_scores_language(language0):
    score_data = scores.get(language0.__class__)(language0)
    assert isinstance(score_data, LanguageScores)
    _test_scores("language", language0, score_data)
    assert (
        score_data.cache_key
        == ("%s.%s.%s"
            % (language0.code,
               timezone.now().date(),
               score_data.revision)))
    qs = score_data.scores_within_days(30)
    assert (
        list(score_data.filter_scores(qs))
        == list(qs.filter(tp__language_id=language0.id)))


@pytest.mark.django_db
def test_scores_project(project0):
    score_data = scores.get(project0.__class__)(project0)
    assert isinstance(score_data, ProjectScores)
    _test_scores("project", project0, score_data)
    assert (
        score_data.cache_key
        == ("%s.%s.%s"
            % (project0.code,
               timezone.now().date(),
               score_data.revision)))
    qs = score_data.scores_within_days(30)
    assert (
        list(score_data.filter_scores(qs))
        == list(qs.filter(tp__project_id=project0.id)))


@pytest.mark.django_db
def test_scores_tp(tp0):
    score_data = scores.get(tp0.__class__)(tp0)
    assert isinstance(score_data, TPScores)
    _test_scores("tp", tp0, score_data)
    assert (
        score_data.cache_key
        == ("%s/%s.%s.%s"
            % (tp0.language.code,
               tp0.project.code,
               timezone.now().date(),
               score_data.revision)))
    qs = score_data.scores_within_days(30)
    assert (
        list(score_data.filter_scores(qs))
        == list(qs.filter(tp_id=tp0.id)))


@pytest.mark.django_db
def test_scores_project_set(project_set):
    score_data = scores.get(project_set.__class__)(project_set)
    assert isinstance(score_data, ProjectSetScores)
    _test_scores("projects", project_set, score_data)
    assert (
        score_data.cache_key
        == ("%s.%s"
            % (timezone.now().date(),
               score_data.revision)))
    qs = score_data.scores_within_days(30)
    assert score_data.filter_scores(qs) is qs

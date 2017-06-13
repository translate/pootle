# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import timedelta

import pytest

from django.contrib.auth import get_user_model
from django.db.models import Sum

from accounts.proxy import DisplayUser
from pootle.core.delegate import revision, scores
from pootle.core.utils.timezone import localdate
from pootle.i18n import formatter
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_score.apps import PootleScoreConfig
from pootle_score.display import TopScoreDisplay
from pootle_score.models import UserTPScore
from pootle_score.utils import (
    LanguageScores, ProjectScores, ProjectSetScores, TPScores, UserScores)


User = get_user_model()


def _test_scores(ns, context, score_data):
    today = localdate()
    assert score_data.context == context
    assert (
        score_data.get_daterange(30)
        == (today - timedelta(days=30), today))
    assert score_data.ns == "pootle.score.%s" % ns
    assert score_data.sw_version == PootleScoreConfig.version
    assert list(score_data.score_model.order_by("id")) == list(
        UserTPScore.objects.exclude(
            user__username__in=User.objects.META_USERS).order_by("id"))
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
                    Sum("translated")).filter(
                        score__sum__gt=0).order_by("-score__sum")))
    assert (
        tuple(score_data.top_scorers)
        == tuple(score_data.get_top_scorers(30)))
    assert (
        score_data.revision
        == revision.get(context.directory.__class__)(
            context.directory).get(key="stats"))

    score_display = score_data.display()
    assert isinstance(score_display, TopScoreDisplay)
    for i, item in enumerate(score_display):
        data = score_data.top_scorers[i]
        assert item["public_total_score"] == formatter.number(
            round(data["score__sum"]))
        assert isinstance(item["user"], DisplayUser)
        assert item["user"].username == data["user__username"]
        assert item["user"].full_name == data["user__full_name"]
        assert item["user"].email == data["user__email"]
    score_display = score_data.display(limit=1)
    assert len(list(score_display)) <= 1


@pytest.mark.django_db
def test_scores_language(language0):
    score_data = scores.get(language0.__class__)(language0)
    assert isinstance(score_data, LanguageScores)
    _test_scores("language", language0, score_data)
    assert (
        score_data.cache_key
        == ("%s.%s.%s"
            % (language0.code,
               localdate(),
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
               localdate(),
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
               localdate(),
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
            % (localdate(),
               score_data.revision)))
    qs = score_data.scores_within_days(30)
    assert score_data.filter_scores(qs) is qs


@pytest.mark.django_db
def test_scores_user(member, system):
    score_data = scores.get(member.__class__)(member)

    assert isinstance(score_data, UserScores)
    assert score_data.ns == "pootle.score.user"
    assert score_data.sw_version == PootleScoreConfig.version
    assert score_data.context == member
    assert score_data.public_score == member.public_score
    assert(
        list(score_data.get_scores_by_language(10))
        == list(
            score_data.get_scores(10).order_by(
                "tp__language").values("tp__language").annotate(Sum("score"))))
    top_lang = score_data.get_scores_by_language(20).order_by("score__sum").first()
    top_lang = Language.objects.get(id=top_lang["tp__language"])
    assert (
        score_data.get_top_language_within(20)
        == top_lang)
    assert (
        score_data.get_language_top_scores(top_lang)
        == scores.get(Language)(top_lang).top_scorers)
    top_lang = score_data.get_top_language_within(100)
    language_scores = score_data.get_language_top_scores(top_lang)
    for index, user_score in enumerate(language_scores):
        if user_score['user__username'] == member.username:
            assert (
                score_data.get_top_language(100)
                == (index + 1, top_lang))
            break
    assert (
        score_data.top_language
        == score_data.get_top_language(30))
    project_directory = Directory.objects.get(pootle_path="/projects/")
    assert (
        score_data.revision
        == revision.get(Directory)(
            project_directory).get(key="stats"))
    assert (
        score_data.cache_key
        == ("%s.%s.%s"
            % (member.id,
               localdate(),
               score_data.revision)))
    # system gets no rank
    sys_score_data = scores.get(system.__class__)(system)
    assert (
        sys_score_data.top_language
        == (-1, None))

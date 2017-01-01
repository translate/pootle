# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils import timezone

from pootle.core.decorators import persistent_property
from pootle.core.delegate import revision
from pootle_app.models import Directory

from .apps import PootleScoreConfig
from .models import UserTPScore

User = get_user_model()


class Scores(object):
    ns = "pootle.score"
    sw_version = PootleScoreConfig.version

    def __init__(self, context):
        self.context = context

    @property
    def revision(self):
        return revision.get(Directory)(
            self.context.directory).get(key="stats")

    @property
    def score_model(self):
        return UserTPScore.objects

    def get_daterange(self, days):
        now = timezone.now().date()
        return now - timedelta(days), now

    def scores_within_days(self, days):
        return self.score_model.filter(
            date__range=self.get_daterange(days))

    def get_scores(self, days):
        return self.filter_scores(self.scores_within_days(days))

    def get_top_scorers(self, days=30):
        """Returns users with the top scores.

        :param days: period of days to account for scores.
        :param limit: limit results to this number of users. Values other
            than positive numbers will return the entire result set.
        """
        return self.get_scores(days).order_by("user__username").values(
            "user__username", "user__email", "user__full_name").annotate(
                Sum("score"),
                Sum("suggested"),
                Sum("reviewed"),
                Sum("translated")).order_by("-score__sum")

    def filter_scores(self, qs):
        return qs

    @persistent_property
    def top_scorers(self):
        return tuple(self.get_top_scorers())


class LanguageScores(Scores):
    ns = "pootle.score.language"

    @property
    def cache_key(self):
        return (
            "%s.%s.%s"
            % (self.context.code,
               timezone.now().date(),
               self.revision))

    def filter_scores(self, qs):
        return qs.filter(tp__language_id=self.context.id)


class ProjectScores(Scores):
    ns = "pootle.score.project"

    @property
    def cache_key(self):
        return (
            "%s.%s.%s"
            % (self.context.code,
               timezone.now().date(),
               self.revision))

    def filter_scores(self, qs):
        return qs.filter(tp__project_id=self.context.id)


class ProjectSetScores(Scores):
    ns = "pootle.score.projects"

    @property
    def cache_key(self):
        return (
            "%s.%s"
            % (timezone.now().date(),
               self.revision))


class TPScores(Scores):
    ns = "pootle.score.tp"

    @property
    def cache_key(self):
        return (
            "%s/%s.%s.%s"
            % (self.context.language.code,
               self.context.project.code,
               timezone.now().date(),
               self.revision))

    def filter_scores(self, qs):
        return qs.filter(tp_id=self.context.id)

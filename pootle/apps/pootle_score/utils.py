# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import date, datetime, timedelta

import pytz

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils.functional import cached_property

from pootle.core.decorators import persistent_property
from pootle.core.delegate import display, revision, scores
from pootle.core.utils.timezone import localdate, make_aware
from pootle_app.models import Directory
from pootle_language.models import Language

from .apps import PootleScoreConfig
from .models import UserTPScore


User = get_user_model()


def to_datetime(possible_dt):
    if possible_dt is None:
        return
    if isinstance(possible_dt, datetime):
        return possible_dt
    if isinstance(possible_dt, date):
        return make_aware(
            datetime.combine(
                possible_dt,
                datetime.min.time())).astimezone(
                    pytz.timezone("UTC"))


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
        return UserTPScore.objects.exclude(
            user__username__in=User.objects.META_USERS)

    def get_daterange(self, days):
        now = localdate()
        return now - timedelta(days), now

    def scores_within_days(self, days):
        return self.score_model.filter(
            date__range=self.get_daterange(days))

    def get_scores(self, days):
        return self.filter_scores(self.scores_within_days(days))

    def get_top_scorers(self, days=30):
        """Returns users with the top scores.

        :param days: period of days to account for scores.
        """
        return self.get_scores(days).order_by("user__username").values(
            "user__username", "user__email", "user__full_name").annotate(
                Sum("score"),
                Sum("suggested"),
                Sum("reviewed"),
                Sum("translated")).filter(
                    score__sum__gt=0).order_by("-score__sum")

    def filter_scores(self, qs):
        return qs

    @persistent_property
    def top_scorers(self):
        return tuple(self.get_top_scorers())

    def display(self, offset=0, limit=5, language=None, formatter=None):
        scorers = self.top_scorers
        if offset or limit:
            scorers = list(scorers)
        if offset:
            scorers = scorers[offset:]
        if limit:
            scorers = scorers[:limit]
        return display.get(Scores)(
            top_scores=scorers,
            formatter=formatter,
            language=language)


class LanguageScores(Scores):
    ns = "pootle.score.language"

    @cached_property
    def cache_key(self):
        return (
            "%s.%s.%s"
            % (self.context.code,
               localdate(),
               self.revision))

    def filter_scores(self, qs):
        return qs.filter(tp__language_id=self.context.id)


class ProjectScores(Scores):
    ns = "pootle.score.project"

    @cached_property
    def cache_key(self):
        return (
            "%s.%s.%s"
            % (self.context.code,
               localdate(),
               self.revision))

    def filter_scores(self, qs):
        return qs.filter(tp__project_id=self.context.id)


class ProjectSetScores(Scores):
    ns = "pootle.score.projects"

    @cached_property
    def cache_key(self):
        return (
            "%s.%s"
            % (localdate(),
               self.revision))


class TPScores(Scores):
    ns = "pootle.score.tp"

    @cached_property
    def cache_key(self):
        return (
            "%s/%s.%s.%s"
            % (self.context.language.code,
               self.context.project.code,
               localdate(),
               self.revision))

    def filter_scores(self, qs):
        return qs.filter(tp_id=self.context.id)


class UserScores(Scores):
    ns = "pootle.score.user"

    @cached_property
    def cache_key(self):
        return (
            "%s.%s.%s"
            % (self.context.id,
               localdate(),
               self.revision))

    @property
    def revision(self):
        return revision.get(Directory)(
            Directory.objects.projects).get(key="stats")

    @property
    def score_model(self):
        return self.context.scores

    @property
    def public_score(self):
        return self.context.public_score

    @persistent_property
    def top_language(self):
        return self.get_top_language()

    def get_top_language_within(self, days):
        top_lang = self.get_scores_by_language(
            days).order_by("score__sum").first()
        if top_lang:
            return Language.objects.get(id=top_lang["tp__language"])

    def get_scores_by_language(self, days):
        """Languages that the user has contributed to in the last `days`,
        and the summary score
        """
        return self.get_scores(days).order_by(
            "tp__language").values("tp__language").annotate(Sum("score"))

    def get_language_top_scores(self, language):
        return scores.get(language.__class__)(language).top_scorers

    def get_top_language(self, days=30):
        """Returns the top language the user has contributed to and its
        position.

        "Top language" is defined as the language with the highest
        aggregate score delta within the last `days` days.

        :param days: period of days to account for scores.
        :return: Tuple of `(position, Language)`. If there's no delta in
            the score for the given period for any of the languages,
            `(-1, None)` is returned.
        """
        language = self.get_top_language_within(days)
        if language:
            # this only gets scores for the last 30 days as that is cached
            language_scores = self.get_language_top_scores(language)
            for index, user_score in enumerate(language_scores):
                if user_score['user__username'] == self.context.username:
                    return index + 1, language
        return -1, language

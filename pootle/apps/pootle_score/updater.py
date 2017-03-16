# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import date, datetime

from django.utils.functional import cached_property

from pootle.core.delegate import log, event_score
from pootle.core.utils.timezone import make_aware
from pootle_log.utils import LogEvent
from pootle_score.models import UserStoreScore


class ScoreUpdater(object):
    event_class = LogEvent

    def __init__(self, context, *args, **kwargs):
        self.context = context

    @cached_property
    def logs(self):
        return log.get(self.context.__class__)(self.context)

    @cached_property
    def scoring(self):
        return event_score.gather(self.event_class)

    def delete_scores(self, scores):
        self.find_existing_scores(
            scores).select_for_update().delete()

    def find_existing_scores(self, scores):
        existing_scores = self.score_model.objects.none()
        score_iterator = self.iterate_scores(scores)
        for timestamp, user, user_scores in score_iterator:
            existing_scores = (
                existing_scores
                | self.score_model.objects.filter(
                    user_id=user,
                    date=timestamp,
                    **{self.related_field: self.context.pk}))
        return existing_scores

    def new_scores(self, scores):
        score_iterator = self.iterate_scores(scores)
        for timestamp, user, user_scores in score_iterator:
            user_scores.update(
                {self.related_field: self.context.pk})
            yield self.score_model(
                date=timestamp,
                user_id=user,
                **user_scores)

    def create_scores(self, scores):
        self.score_model.objects.bulk_create(self.new_scores(scores))

    def set_scores(self, calculated_scores):
        self.delete_scores(calculated_scores)
        self.create_scores(calculated_scores)

    def update(self):
        self.set_scores(self.calculate())


class StoreScoreUpdater(ScoreUpdater):
    score_model = UserStoreScore
    related_field = "store_id"

    def __init__(self, *args, **kwargs):
        self.user = kwargs.get('user')
        super(StoreScoreUpdater, self).__init__(*args, **kwargs)

    @property
    def store(self):
        return self.context

    def score_event(self, event, calculated_scores):
        if event.action not in self.scoring:
            return
        scores = self.scoring[event.action](event).get_score()
        if not scores or not any(x > 0 for x in scores.values()):
            return
        calculated_scores[event.timestamp] = (
            calculated_scores.get(event.timestamp, {}))
        calculated_scores[event.timestamp][event.user.id] = (
            calculated_scores[event.timestamp].get(event.user.id, {}))
        for k, score in scores.items():
            if not score:
                continue
            calculated_scores[event.timestamp][event.user.id][k] = (
                calculated_scores[event.timestamp][event.user.id].get(k, 0)
                + score)

    def calculate(self, start=None, end=None):
        if start is None:
            start = make_aware(
                datetime.combine(
                    date.today(),
                    datetime.min.time()))
        calculated_scores = {}
        scored_events = self.logs.get_events(
            user=self.user, start=start, end=end)
        for event in scored_events:
            self.score_event(event, calculated_scores)
        return calculated_scores

    def iterate_scores(self, scores):
        for timestamp, date_scores in scores.items():
            for user, user_scores in date_scores.items():
                yield timestamp, user, user_scores

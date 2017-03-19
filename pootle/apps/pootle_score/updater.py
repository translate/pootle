# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import date

from django.contrib.auth import get_user_model
from django.db.models import Sum
from django.utils.functional import cached_property

from pootle.core.delegate import log, event_score
from pootle.core.signals import update_scores
from pootle_log.utils import LogEvent
from pootle_score.models import UserStoreScore, UserTPScore


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

    def filter_users(self, qs, users):
        field = "user_id"
        if not users:
            return qs
        return (
            qs.filter(**{field: list(users).pop()})
            if len(users) == 1
            else qs.filter(**{"%s__in" % field: users}))

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
        return self.score_model.objects.bulk_create(self.new_scores(scores))

    def set_scores(self, calculated_scores):
        self.delete_scores(calculated_scores)
        return self.create_scores(calculated_scores)

    def update(self, users=None):
        return self.set_scores(self.calculate(users=users))


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
        calculated_scores[event.timestamp.date()] = (
            calculated_scores.get(event.timestamp.date(), {}))
        calculated_scores[event.timestamp.date()][event.user.id] = (
            calculated_scores[event.timestamp.date()].get(event.user.id, {}))
        for k, score in scores.items():
            if not score:
                continue
            calculated_scores[event.timestamp.date()][event.user.id][k] = (
                calculated_scores[event.timestamp.date()][event.user.id].get(k, 0)
                + score)

    def calculate(self, start=None, end=None, users=None):
        calculated_scores = {}
        scored_events = self.logs.get_events(
            users=users, start=start, end=end)
        for event in scored_events:
            self.score_event(event, calculated_scores)
        return calculated_scores

    def iterate_scores(self, scores):
        for timestamp, date_scores in scores.items():
            for user, user_scores in date_scores.items():
                yield timestamp, user, user_scores

    def update(self, users=None):
        updated = super(StoreScoreUpdater, self).update(users=users)
        if updated:
            update_scores.send(
                self.store.translation_project.__class__,
                instance=self.store.translation_project,
                users=set([x.user_id for x in updated]))
        return updated


class TPScoreUpdater(ScoreUpdater):
    related_field = "tp_id"
    score_model = UserTPScore
    store_score_model = UserStoreScore

    @property
    def tp(self):
        return self.context

    def iterate_scores(self, scores):
        score_values = scores.values(
            "date",
            "user_id",
            "score",
            "translated",
            "reviewed",
            "suggested")
        for score in score_values.iterator():
            yield (
                score.pop("date"),
                score.pop("user_id"),
                score)

    def calculate(self, start=None, end=None, users=None):
        qs = self.filter_users(
            self.store_score_model.objects.filter(
                store__translation_project=self.tp),
            users)
        return qs.order_by(
            "date", "user").values_list(
                "date", "user").annotate(
                    score=Sum("score"),
                    translated=Sum("translated"),
                    reviewed=Sum("reviewed"),
                    suggested=Sum("suggested"))

    def update(self, users=None):
        updated = super(TPScoreUpdater, self).update(users=users)
        if updated:
            update_scores.send(
                get_user_model(),
                users=set([x.user_id for x in updated]))
        return updated


class UserScoreUpdater(ScoreUpdater):
    tp_score_model = UserTPScore
    store_score_model = UserStoreScore
    score_model = get_user_model()

    def __init__(self, users=None, **kwargs):
        self.users = users

    def calculate(self, start=date.today(), end=None, **kwargs):
        return self.filter_users(
            self.tp_score_model.objects,
            self.users).order_by("user").values_list(
                "user").annotate(score=Sum("score"))

    def set_scores(self, calculated_scores):
        for user, score in calculated_scores:
            self.score_model.objects.filter(id=user).update(score=score)

    def clear(self):
        tp_scores = self.tp_score_model.objects.all()
        store_scores = self.store_score_model.objects.all()
        scores = self.score_model.objects.all()
        if self.users:
            tp_scores = tp_scores.filter(user_id__in=self.users)
            store_scores = store_scores.filter(user_id__in=self.users)
            scores = scores.filter(id__in=self.users)
        tp_scores.delete()
        store_scores.delete()
        scores.update(score=0)

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import timedelta

from mock import PropertyMock, patch

import pytest

from django.db.models import Sum

from pootle.core.delegate import event_score, score_updater
from pootle.core.plugin import provider
from pootle.core.plugin.results import GatheredDict
from pootle.core.utils.timezone import localdate
from pootle_log.utils import LogEvent, StoreLog
from pootle_score.models import UserStoreScore
from pootle_score.updater import (
    StoreScoreUpdater, TPScoreUpdater, UserScoreUpdater)
from pootle_score.utils import to_datetime
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject


GET_EVENT_KWARGS = {
    'end': None,
    'users': None,
    'event_sources': ('suggestion', 'submission'),
    'include_meta': False,
    'start': None,
    'only': {
        'submission': (
            'unit__unit_source__source_wordcount',
            'unit__unit_source__created_by_id',
            'unit_id',
            'submitter__id',
            'old_value',
            'new_value',
            'creation_time',
            'revision',
            'field'),
        'suggestion': (
            'unit__unit_source__source_wordcount',
            'user_id',
            'reviewer_id',
            'state_id')},
    'ordered': False}


@pytest.mark.django_db
def test_score_store_updater(store0, admin):
    updater = score_updater.get(Store)(store0)
    assert updater.store == store0
    assert updater.user is None
    assert isinstance(updater, StoreScoreUpdater)
    assert isinstance(updater.logs, StoreLog)
    assert updater.event_class == LogEvent
    assert isinstance(updater.scoring, GatheredDict)
    updater = score_updater.get(Store)(store0, user=admin)
    assert updater.user == admin


@pytest.mark.django_db
@patch('pootle_score.updater.StoreScoreUpdater.logs', new_callable=PropertyMock)
def test_score_store_updater_event(logs_mock, store0, admin, member,
                                   today, yesterday):
    unit0 = store0.units[0]
    unit1 = store0.units[1]
    _events = [
        LogEvent(unit0, admin, today, "action0", 0),
        LogEvent(unit0, admin, yesterday, "action1", 1),
        LogEvent(unit1, member, today, "action2", 2)]

    def _get_events(start=None, end=None, **kwargs):
        for event in _events:
            yield event

    logs_mock.configure_mock(
        **{'return_value.get_events.side_effect': _get_events})

    updater = StoreScoreUpdater(store0)
    result = updater.calculate()
    assert (
        list(logs_mock.return_value.get_events.call_args)
        == [(), GET_EVENT_KWARGS])
    # no score adapters
    assert result == {}
    result = updater.calculate(start=yesterday, end=today)
    kwargs = GET_EVENT_KWARGS.copy()
    kwargs['start'] = to_datetime(yesterday)
    kwargs['end'] = to_datetime(today)
    assert (
        list(logs_mock.return_value.get_events.call_args)
        == [(), kwargs])
    assert result == {}
    updater = StoreScoreUpdater(store0)
    updater.calculate(users=(admin, ))
    kwargs = GET_EVENT_KWARGS.copy()
    kwargs['users'] = (admin, )
    assert (
        list(logs_mock.return_value.get_events.call_args)
        == [(), kwargs])
    updater.calculate(users=(admin, member))
    kwargs['users'] = (admin, member)
    assert (
        list(logs_mock.return_value.get_events.call_args)
        == [(), kwargs])


@pytest.mark.django_db
@patch('pootle_score.updater.StoreScoreUpdater.logs', new_callable=PropertyMock)
def test_score_store_updater_event_score(logs_mock, store0,
                                         admin, member, member2,
                                         today, yesterday,
                                         dt_today, dt_yesterday):
    unit0 = store0.units[0]
    unit1 = store0.units[1]
    _events = [
        LogEvent(unit0, admin, dt_yesterday, "action0", 0),
        LogEvent(unit0, admin, dt_yesterday, "action1", 1),
        LogEvent(unit0, admin, dt_today, "action0", 0),
        LogEvent(unit0, member2, dt_today, "action1", 1),
        LogEvent(unit0, member, dt_today, "action2", 2),
        LogEvent(unit1, member, dt_today, "action2", 3)]

    def _get_events(start=None, end=None, **kwargs):
        for event in _events:
            yield event

    logs_mock.configure_mock(
        **{'return_value.get_events.side_effect': _get_events})
    updater = StoreScoreUpdater(store0)
    result = updater.calculate()
    assert result == {}

    class DummyScore(object):

        def __init__(self, event):
            self.event = event

        def get_score(self):
            return dict(
                score=(self.event.value * self.base_score),
                translated=(7 * self.base_score),
                reviewed=(23 * self.base_score),
                suggested=(108 * self.base_score))

    class Action0Score(DummyScore):
        base_score = 0

    class Action1Score(DummyScore):
        base_score = 1

    class Action2Score(DummyScore):
        base_score = 2

        def get_score(self):
            score = super(Action2Score, self).get_score()
            score["reviewed"] = 0
            return score

    @provider(event_score, sender=LogEvent)
    def dummy_event_score_provider(**kwargs_):
        return dict(
            action0=Action0Score,
            action1=Action1Score,
            action2=Action2Score)

    updater = StoreScoreUpdater(store0)
    result = updater.calculate()
    assert len(result) == 2
    assert len(result[today]) == 2
    assert result[today][member.id] == {
        'suggested': 432,
        'score': 10,
        'translated': 28}
    assert result[today][member2.id] == {
        'suggested': 108,
        'score': 1,
        'translated': 7,
        'reviewed': 23}
    assert len(result[yesterday]) == 1
    assert result[yesterday][admin.id] == {
        'suggested': 108,
        'score': 1,
        'translated': 7,
        'reviewed': 23}
    store0.user_scores.all().delete()
    updater.update()
    mem_score = UserStoreScore.objects.filter(
        store=store0, user=member)
    assert mem_score.get(date=today).suggested == 432
    assert mem_score.get(date=today).score == 10
    assert mem_score.get(date=today).translated == 28
    assert mem_score.get(date=today).reviewed == 0
    today_score = mem_score.get(date=today)
    today_score.reviewed = 99999
    today_score.score = 0
    today_score.save()
    updater.update()
    assert mem_score.get(date=today).suggested == 432
    assert mem_score.get(date=today).score == 10
    assert mem_score.get(date=today).translated == 28
    assert mem_score.get(date=today).reviewed == 0


@pytest.mark.django_db
def test_score_tp_updater(tp0, admin, member, member2):
    updater = score_updater.get(TranslationProject)(tp0)
    assert updater.tp == tp0
    assert isinstance(updater, TPScoreUpdater)


@pytest.fixture
def create_score_data(today, yesterday, admin, member, member2):
    def _generate_data(store):
        data = {}
        data[today] = dict()
        data[yesterday] = dict()
        for user in [admin, member, member2]:
            data[today][user.id] = dict(
                score=(store.id * user.id),
                suggested=(2 * store.id * user.id),
                translated=(3 * store.id * user.id),
                reviewed=(4 * store.id * user.id))
            data[yesterday][user.id] = dict(
                score=(5 * store.id * user.id),
                suggested=(6 * store.id * user.id),
                translated=(7 * store.id * user.id),
                reviewed=(8 * store.id * user.id))
        return data
    return _generate_data


@pytest.mark.django_db
def test_score_tp_updater_update(store0, tp0, admin, member, member2,
                                 today, yesterday, create_score_data):
    updater = score_updater.get(TranslationProject)(tp0)
    store1 = tp0.stores.exclude(id=store0.id).first()

    tp0.user_scores.all().delete()
    UserStoreScore.objects.filter(store__translation_project=tp0).delete()
    score_updater.get(Store)(store0).set_scores(create_score_data(store0))
    score_updater.get(Store)(store1).set_scores(create_score_data(store1))
    updater.update()
    for user in [admin, member, member2]:
        scores_today = tp0.user_scores.get(date=today, user=user)
        assert scores_today.score == (
            (store0.id * user.id)
            + (store1.id * user.id))
        assert scores_today.suggested == (
            (2 * store0.id * user.id)
            + (2 * store1.id * user.id))
        assert scores_today.translated == (
            (3 * store0.id * user.id)
            + (3 * store1.id * user.id))
        assert scores_today.reviewed == (
            (4 * store0.id * user.id)
            + (4 * store1.id * user.id))
        scores_yesterday = tp0.user_scores.get(date=yesterday, user=user)
        assert scores_yesterday.score == (
            (5 * store0.id * user.id)
            + (5 * store1.id * user.id))
        assert scores_yesterday.suggested == (
            (6 * store0.id * user.id)
            + (6 * store1.id * user.id))
        assert scores_yesterday.translated == (
            (7 * store0.id * user.id)
            + (7 * store1.id * user.id))
        assert scores_yesterday.reviewed == (
            (8 * store0.id * user.id)
            + (8 * store1.id * user.id))


@pytest.mark.django_db
def test_score_user_updater_calculate(tp0, admin, member):
    user_updater = score_updater.get(admin.__class__)
    admin.score = -999
    admin.save()
    member.score = -777
    member.save()
    assert user_updater == UserScoreUpdater
    updater = user_updater(users=[admin, member])
    assert updater.users == [admin, member]
    result = updater.calculate()
    admin_score = admin.scores.filter(
        date__gte=(
            localdate()
            - timedelta(days=30)))
    admin_score = round(sum(
        admin_score.values_list(
            "score", flat=True)), 2)
    member_score = member.scores.filter(
        date__gte=(
            localdate()
            - timedelta(days=30)))
    member_score = round(sum(
        member_score.values_list(
            "score", flat=True)), 2)
    assert round(dict(result)[admin.pk], 2) == admin_score
    assert round(dict(result)[member.pk], 2) == member_score
    updater.set_scores(result)
    admin.refresh_from_db()
    member.refresh_from_db()
    assert round(admin.score, 2) == admin_score
    assert round(member.score, 2) == member_score
    admin.score = -999
    admin.save()
    updater = user_updater((admin, ))
    assert updater.users == (admin, )
    result = updater.calculate()
    assert round(dict(result)[admin.pk], 2) == admin_score
    updater.set_scores(result)
    admin.refresh_from_db()
    assert round(admin.score, 2) == admin_score


@pytest.mark.django_db
def test_score_user_updater_refresh(tp0, admin, member):
    user_updater = score_updater.get(admin.__class__)
    updater = user_updater((admin, ))
    admin_score = admin.score
    admin.score = 0
    admin.save()
    member_score = member.score
    member.score = 0
    member.save()

    updater.refresh_scores()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert admin.score == admin_score
    assert member.score == member_score

    admin.score = 0
    admin.save()
    member.score = 0
    member.save()
    updater.refresh_scores(users=[admin])
    member.refresh_from_db()
    admin.refresh_from_db()
    assert admin.score == admin_score
    assert member.score == 0


@pytest.mark.django_db
def test_score_tp_updater_clear(tp0, admin, member):
    tp_scores = tp0.user_scores.filter(
        date__gte=localdate() - timedelta(days=30))
    updater = TPScoreUpdater(tp0)
    admin_score = admin.score
    member_score = member.score
    admin_tp_score = tp_scores.filter(
        user=admin).aggregate(score=Sum('score'))['score']
    member_tp_score = tp_scores.filter(
        user=member).aggregate(score=Sum('score'))['score']
    updater.clear()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert (
        round(admin.score, 2)
        == round(admin_score - admin_tp_score, 2))
    assert (
        round(member.score, 2)
        == round(member_score - member_tp_score, 2))


@pytest.mark.django_db
def test_score_tp_updater_clear_users(tp0, admin, member):
    tp_scores = tp0.user_scores.filter(
        date__gte=localdate() - timedelta(days=30))
    updater = TPScoreUpdater(tp0)
    admin_score = admin.score
    member_score = member.score
    member_tp_score = tp_scores.filter(
        user=member).aggregate(score=Sum('score'))['score']
    updater.clear(users=[member.id])
    member.refresh_from_db()
    admin.refresh_from_db()
    assert admin.score == admin_score
    assert (
        round(member.score, 2)
        == round(member_score - member_tp_score, 2))

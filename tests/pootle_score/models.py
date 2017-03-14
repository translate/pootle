# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from datetime import timedelta

from django.db.utils import IntegrityError
from django.utils import timezone

from pootle_score.models import UserStoreScore, UserTPScore


@pytest.mark.django_db
def test_user_tp_score_repr(tp0, member):
    score = UserTPScore.objects.create(
        user=member,
        tp=tp0,
        score=2,
        date=timezone.now().date() + timedelta(days=5))
    score_info = (
        "%s(%s) %s score: %s, suggested: %s, translated: %s, reviewed: %s"
        % (score.user.username,
           score.tp.pootle_path,
           score.date,
           score.score,
           score.suggested,
           score.translated,
           score.reviewed))
    assert str(score) == score_info
    assert repr(score) == u"<UserTPScore: %s>" % score_info


@pytest.mark.django_db
def test_user_tp_score_instance(tp0, member):
    theday = timezone.now().date() + timedelta(days=5)
    score = UserTPScore.objects.create(
        user=member, tp=tp0, score=2, date=theday)
    assert score.user == member
    assert score.tp == tp0
    assert score.date == theday
    assert score.score is 2
    assert score.suggested is 0
    assert score.translated is 0
    assert score.reviewed is 0
    score.score = -3
    score.suggested = 1
    score.translated = 4
    score.reviewed = 10005
    score.save()


@pytest.mark.django_db
def test_user_tp_score_bad_no_user(tp0, member):
    with pytest.raises(IntegrityError):
        UserTPScore.objects.create(
            tp=tp0,
            score=2,
            date=timezone.now().date() + timedelta(days=5))


@pytest.mark.django_db
def test_user_tp_score_bad_no_tp(tp0, member):
    with pytest.raises(IntegrityError):
        UserTPScore.objects.create(
            user=member,
            score=2,
            date=timezone.now().date() + timedelta(days=5))


@pytest.mark.django_db
def test_user_tp_score_bad_no_date(tp0, member):
    with pytest.raises(IntegrityError):
        UserTPScore.objects.create(
            user=member, tp=tp0, score=2)


@pytest.mark.django_db
def test_user_tp_score_bad_dupe(tp0, member):
    theday = timezone.now().date() + timedelta(days=5)
    UserTPScore.objects.create(
        user=member, tp=tp0, score=2, date=theday)
    with pytest.raises(IntegrityError):
        UserTPScore.objects.create(
            user=member, tp=tp0, score=3, date=theday)


@pytest.mark.django_db
def test_user_store_score_repr(store0, member):
    score = UserStoreScore.objects.create(
        user=member,
        store=store0,
        score=2,
        date=timezone.now().date() + timedelta(days=5))
    score_info = (
        "%s(%s) %s score: %s, suggested: %s, translated: %s, reviewed: %s"
        % (score.user.username,
           score.store.pootle_path,
           score.date,
           score.score,
           score.suggested,
           score.translated,
           score.reviewed))
    assert str(score) == score_info
    assert repr(score) == u"<UserStoreScore: %s>" % score_info

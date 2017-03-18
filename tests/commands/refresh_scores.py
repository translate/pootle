# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command

from pootle.core.contextmanagers import keep_data
from pootle.core.delegate import review


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_recalculate(capfd, store0, member):
    """Recalculate scores."""
    # delete the 2 most prolific contribs to speed up
    unit = store0.units.filter(suggestion__state__name="pending").first()
    suggestion = unit.suggestion_set.filter(state__name="pending").first()
    member_score = member.score
    with keep_data():
        review.get(suggestion.__class__)(
            [suggestion], reviewer=member).accept()
    member.refresh_from_db()
    assert member.score == member_score
    call_command('refresh_scores')
    member.refresh_from_db()
    assert member.score > member_score


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_recalculate_user(capfd, member, admin):
    """Recalculate scores for given users."""
    member_score = round(member.score, 2)
    member.score = 777
    admin.score = 999
    member.save()
    admin.save()
    call_command('refresh_scores', '--user=member')
    admin.refresh_from_db()
    member.refresh_from_db()
    assert round(member.score, 2) == member_score
    assert admin.score == 999


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_reset_user(capfd, member, admin):
    """Set scores to zero for given users."""
    admin_score = round(admin.score, 2)
    call_command('refresh_scores', '--reset', '--user=member')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert member.score == 0
    assert member.scores.count() == 0
    assert member.store_scores.count() == 0
    assert admin_score == round(admin.score, 2)


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_reset(capfd, admin, member):
    """Set scores to zero."""
    call_command('refresh_scores', '--reset')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert member.score == 0
    assert member.scores.count() == 0
    assert member.store_scores.count() == 0
    assert admin.score == 0
    assert admin.scores.count() == 0
    assert admin.store_scores.count() == 0

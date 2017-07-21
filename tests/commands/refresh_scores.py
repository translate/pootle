# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.contrib.auth import get_user_model
from django.core.management import call_command

from pootle.core.contextmanagers import keep_data
from pootle.core.delegate import review, score_updater


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
    call_command('refresh_scores', '--reset', '--user=member')
    call_command('refresh_scores', '--user=member')
    member.refresh_from_db()
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
    call_command('refresh_scores', '--reset', '--user=member')
    call_command('refresh_scores', '--user=member')
    call_command('refresh_scores', '--reset', '--user=admin')
    call_command('refresh_scores', '--user=admin')
    member.refresh_from_db()
    admin.refresh_from_db()
    admin_score = round(admin.score, 2)
    member_score = round(member.score, 2)
    call_command('refresh_scores', '--reset', '--user=member')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert member.score == 0
    assert member.scores.count() == 0
    assert member.store_scores.count() == 0
    assert admin_score == round(admin.score, 2)
    call_command('refresh_scores', '--user=member')
    member.refresh_from_db()
    assert round(member.score, 2) == member_score


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


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_project(capfd, admin, member, project0):
    """Reset and set again scores for a project."""
    member.refresh_from_db()
    admin.refresh_from_db()
    updater = score_updater.get(get_user_model())()
    member_score = updater.calculate(users=[member]).first()[1]
    admin_score = updater.calculate(users=[admin]).first()[1]
    member_scores_count = member.scores.filter(tp__project=project0).count()
    admin_scores_count = admin.scores.filter(tp__project=project0).count()
    member_store_scores_count = member.store_scores.filter(
        store__translation_project__project=project0).count()
    admin_store_scores_count = admin.store_scores.filter(
        store__translation_project__project=project0).count()

    call_command('refresh_scores', '--reset', '--project=project0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert member.score == 0
    assert member.scores.filter(tp__project=project0).count() == 0
    assert member.store_scores.filter(
        store__translation_project__project=project0).count() == 0
    assert admin.score == 0
    assert admin.scores.filter(tp__project=project0).count() == 0
    assert admin.store_scores.filter(
        store__translation_project__project=project0).count() == 0

    call_command('refresh_scores', '--project=project0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert round(member.score, 2) == round(member_score, 2)
    assert (member.scores.filter(tp__project=project0).count() ==
            member_scores_count)
    assert (member.store_scores.filter(
        store__translation_project__project=project0).count() ==
        member_store_scores_count)
    assert round(admin.score, 2) == round(admin_score, 2)
    assert (admin.scores.filter(tp__project=project0).count() ==
            admin_scores_count)
    assert (admin.store_scores.filter(
        store__translation_project__project=project0).count() ==
        admin_store_scores_count)


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_language(capfd, admin, member, language0):
    """Reset and set again scores for a language."""
    member.refresh_from_db()
    admin.refresh_from_db()
    updater = score_updater.get(get_user_model())()
    member_score = updater.calculate(users=[member]).first()[1]
    admin_score = updater.calculate(users=[admin]).first()[1]
    member_scores_count = member.scores.filter(tp__language=language0).count()
    admin_scores_count = admin.scores.filter(tp__language=language0).count()
    member_store_scores_count = member.store_scores.filter(
        store__translation_project__language=language0).count()
    admin_store_scores_count = admin.store_scores.filter(
        store__translation_project__language=language0).count()

    call_command('refresh_scores', '--reset', '--language=language0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert member.score == 0
    assert member.scores.filter(
        tp__language=language0,
        tp__project__disabled=False).count() == 0
    assert member.store_scores.filter(
        store__translation_project__language=language0,
        store__translation_project__project__disabled=False).count() == 0
    assert admin.score == 0
    assert admin.scores.filter(
        tp__language=language0,
        tp__project__disabled=False).count() == 0
    assert admin.store_scores.filter(
        store__translation_project__language=language0,
        store__translation_project__project__disabled=False).count() == 0

    call_command('refresh_scores', '--language=language0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert round(member.score, 2) == round(member_score, 2)
    assert (member.scores.filter(tp__language=language0).count() ==
            member_scores_count)
    assert (member.store_scores.filter(
        store__translation_project__language=language0).count() ==
        member_store_scores_count)
    assert round(admin.score, 2) == round(admin_score, 2)
    assert (admin.scores.filter(tp__language=language0).count() ==
            admin_scores_count)
    assert (admin.store_scores.filter(
        store__translation_project__language=language0).count() ==
        admin_store_scores_count)


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_reset_tp(capfd, admin, member, tp0):
    """Reset and set again scores for a TP."""
    member.refresh_from_db()
    admin.refresh_from_db()
    updater = score_updater.get(get_user_model())()
    member_score = updater.calculate(users=[member]).first()[1]
    admin_score = updater.calculate(users=[admin]).first()[1]
    member_scores_count = member.scores.filter(tp=tp0).count()
    admin_scores_count = admin.scores.filter(tp=tp0).count()
    member_store_scores_count = member.store_scores.filter(
        store__translation_project=tp0).count()
    admin_store_scores_count = admin.store_scores.filter(
        store__translation_project=tp0).count()

    call_command('refresh_scores', '--reset', '--project=project0',
                 '--language=language0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert member.score == 0
    assert member.scores.filter(tp=tp0).count() == 0
    assert member.store_scores.filter(
        store__translation_project=tp0).count() == 0
    assert admin.score == 0
    assert admin.scores.filter(tp=tp0).count() == 0
    assert admin.store_scores.filter(
        store__translation_project=tp0).count() == 0

    call_command('refresh_scores', '--project=project0',
                 '--language=language0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert round(member.score, 2) == round(member_score, 2)
    assert member.scores.filter(tp=tp0).count() == member_scores_count
    assert (member.store_scores.filter(
        store__translation_project=tp0).count() ==
        member_store_scores_count)
    assert round(admin.score, 2) == round(admin_score, 2)
    assert admin.scores.filter(tp=tp0).count() == admin_scores_count
    assert (admin.store_scores.filter(
        store__translation_project=tp0).count() ==
        admin_store_scores_count)


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_user_project(capfd, admin, member, project0):
    """Reset and set again scores for particular user in project."""
    member.refresh_from_db()
    admin.refresh_from_db()
    updater = score_updater.get(get_user_model())()
    member_score = updater.calculate(users=[member]).first()[1]
    admin_score = admin.score
    member_scores_count = member.scores.filter(tp__project=project0).count()
    admin_scores_count = admin.scores.count()
    member_store_scores_count = member.store_scores.filter(
        store__translation_project__project=project0).count()
    admin_store_scores_count = admin.store_scores.count()

    call_command('refresh_scores', '--reset', '--user=member',
                 '--project=project0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert member.score == 0
    assert member.scores.filter(tp__project=project0).count() == 0
    assert member.store_scores.filter(
        store__translation_project__project=project0).count() == 0
    assert admin.score == admin_score
    assert admin.scores.count() == admin_scores_count
    assert admin.store_scores.count() == admin_store_scores_count

    call_command('refresh_scores', '--user=member', '--project=project0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert round(member.score, 2) == round(member_score, 2)
    assert (member.scores.filter(tp__project=project0).count() ==
            member_scores_count)
    assert (member.store_scores.filter(
        store__translation_project__project=project0).count() ==
        member_store_scores_count)
    assert round(admin.score, 2) == round(admin_score, 2)


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_user_language(capfd, admin, member, language0):
    """Reset and set again scores for particular user in language."""
    member.refresh_from_db()
    admin.refresh_from_db()
    updater = score_updater.get(get_user_model())()
    member_score = updater.calculate(users=[member]).first()[1]
    admin_score = admin.score
    member_scores_count = member.scores.filter(
        tp__language=language0,
        tp__project__disabled=False).count()
    admin_scores_count = admin.scores.count()
    member_store_scores_count = member.store_scores.filter(
        store__translation_project__language=language0,
        store__translation_project__project__disabled=False).count()
    admin_store_scores_count = admin.store_scores.count()

    call_command('refresh_scores', '--reset', '--user=member',
                 '--language=language0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert member.score == 0
    assert member.scores.filter(
        tp__language=language0,
        tp__project__disabled=False).count() == 0
    assert member.store_scores.filter(
        store__translation_project__language=language0,
        store__translation_project__project__disabled=False).count() == 0
    assert admin.score == admin_score
    assert admin.scores.count() == admin_scores_count
    assert admin.store_scores.count() == admin_store_scores_count

    call_command('refresh_scores', '--user=member', '--language=language0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert round(member.score, 2) == round(member_score, 2)
    assert (member.scores.filter(
        tp__language=language0,
        tp__project__disabled=False).count() == member_scores_count)
    assert (member.store_scores.filter(
        store__translation_project__language=language0,
        store__translation_project__project__disabled=False).count() ==
        member_store_scores_count)
    assert round(admin.score, 2) == round(admin_score, 2)


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_user_tp(capfd, admin, member, tp0):
    """Reset and set again scores for particular user in TP."""
    member.refresh_from_db()
    admin.refresh_from_db()
    updater = score_updater.get(get_user_model())()
    member_score = updater.calculate(users=[member]).first()[1]
    admin_score = admin.score
    member_scores_count = member.scores.filter(tp=tp0).count()
    admin_scores_count = admin.scores.count()
    member_store_scores_count = member.store_scores.filter(
        store__translation_project=tp0).count()
    admin_store_scores_count = admin.store_scores.count()

    call_command('refresh_scores', '--reset', '--user=member',
                 '--project=project0', '--language=language0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert member.score == 0
    assert member.scores.filter(tp=tp0).count() == 0
    assert member.store_scores.filter(
        store__translation_project=tp0).count() == 0
    assert admin.score == admin_score
    assert admin.scores.count() == admin_scores_count
    assert admin.store_scores.count() == admin_store_scores_count

    call_command('refresh_scores', '--user=member', '--project=project0',
                 '--language=language0')
    out, err = capfd.readouterr()
    member.refresh_from_db()
    admin.refresh_from_db()
    assert round(member.score, 2) == round(member_score, 2)
    assert member.scores.filter(tp=tp0).count() == member_scores_count
    assert (member.store_scores.filter(
        store__translation_project=tp0).count() ==
        member_store_scores_count)
    assert round(admin.score, 2) == round(admin_score, 2)

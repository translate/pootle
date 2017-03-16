# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.db.models.signals import post_save
from django.dispatch import receiver

from pootle.core.delegate import score_updater
from pootle.core.signals import update_scores
from pootle_statistics.models import (
    ScoreLog, Submission, TranslationActionCodes)
from pootle_store.models import Store, Suggestion
from pootle_translationproject.models import TranslationProject


from .models import UserStoreScore


@receiver(update_scores, sender=TranslationProject)
def update_store_scores_handler(**kwargs):
    tp = kwargs["instance"]
    score_updater.get(tp.__class__)(tp).update()


@receiver(update_scores, sender=Store)
def update_tp_scores_handler(**kwargs):
    store = kwargs["instance"]
    score_updater.get(store.__class__)(store).update()


@receiver(post_save, sender=UserStoreScore)
def handle_store_score_updated(**kwargs):
    tp = kwargs["instance"].store.translation_project
    update_scores.send(tp.__class__, instance=tp)


@receiver(post_save, sender=Suggestion)
def handle_suggestion_change(**kwargs):
    suggestion = kwargs["instance"]
    is_system_user = (
        (suggestion.state.name == "pending"
         and (suggestion.user
              == get_user_model().objects.get_system_user()))
        or (suggestion.state.name != "pending"
            and (suggestion.reviewer
                 == get_user_model().objects.get_system_user())))
    if is_system_user:
        return
    update_scores.send(
        suggestion.unit.store.__class__,
        instance=suggestion.unit.store)


@receiver(post_save, sender=Submission)
def handle_submission_added(**kwargs):
    submission = kwargs["instance"]
    is_system_user = (
        submission.submitter
        == get_user_model().objects.get_system_user())
    if is_system_user:
        return
    update_scores.send(
        submission.unit.store.__class__,
        instance=submission.unit.store)


@receiver(post_save, sender=ScoreLog)
def handle_scorelog_save(**kwargs):
    scorelog = kwargs["instance"]
    tp = scorelog.submission.translation_project
    created = False
    changed = dict(suggested=0, translated=0, reviewed=0)
    review_actions = [
        TranslationActionCodes.SUGG_REVIEWED_ACCEPTED,
        TranslationActionCodes.REVIEWED,
        TranslationActionCodes.EDITED]
    if scorelog.translated_wordcount is not None:
        changed["translated"] = scorelog.translated_wordcount
    elif scorelog.action_code in review_actions:
        changed["reviewed"] = scorelog.wordcount
    try:
        user_score = tp.user_scores.get(
            date=scorelog.creation_time.date(),
            user=scorelog.user)
    except tp.user_scores.model.DoesNotExist:
        user_score = tp.user_scores.create(
            date=scorelog.creation_time.date(),
            user=scorelog.user,
            score=scorelog.score_delta,
            **changed)
        created = True
    if not created:
        user_score.score += scorelog.score_delta
        for k, v in changed.items():
            existing = getattr(user_score, k)
            if v is not 0:
                setattr(user_score, k, existing + v)
        user_score.save()

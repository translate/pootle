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

from pootle.core.delegate import crud, score_updater
from pootle.core.signals import create, update, update_scores
from pootle.core.utils.timezone import localdate
from pootle_statistics.models import Submission
from pootle_store.models import Store, Suggestion
from pootle_translationproject.models import TranslationProject

from .models import UserStoreScore, UserTPScore


@receiver(update, sender=UserStoreScore)
def handle_store_score_update(**kwargs):
    crud.get(UserStoreScore).update(**kwargs)


@receiver(create, sender=UserStoreScore)
def handle_user_store_score_create(**kwargs):
    crud.get(UserStoreScore).create(**kwargs)


@receiver(update, sender=UserTPScore)
def handle_user_tp_score_update(**kwargs):
    crud.get(UserTPScore).update(**kwargs)


@receiver(create, sender=UserTPScore)
def handle_user_tp_score_create(**kwargs):
    crud.get(UserTPScore).create(**kwargs)


@receiver(update_scores, sender=get_user_model())
def update_user_scores_handler(**kwargs):
    score_updater.get(get_user_model())().update(
        users=kwargs.get("users"),
        date=kwargs.get("date"))


@receiver(update_scores, sender=TranslationProject)
def update_tp_scores_handler(**kwargs):
    tp = kwargs["instance"]
    score_updater.get(tp.__class__)(tp).update(
        users=kwargs.get("users"),
        date=kwargs.get("date"))


@receiver(update_scores, sender=Store)
def update_store_scores_handler(**kwargs):
    store = kwargs["instance"]
    score_updater.get(store.__class__)(store).update(
        users=kwargs.get("users"),
        date=kwargs.get("date"))


@receiver(post_save, sender=UserStoreScore)
def handle_store_score_updated(**kwargs):
    tp = kwargs["instance"].store.translation_project
    update_scores.send(
        tp.__class__,
        instance=tp,
        users=[kwargs["instance"].user_id],
        date=kwargs["instance"].date)


@receiver(post_save, sender=Suggestion)
def handle_suggestion_change(**kwargs):
    suggestion = kwargs["instance"]
    is_system_user = (
        (suggestion.is_pending
         and (suggestion.user_id
              == get_user_model().objects.get_system_user().id))
        or (not suggestion.is_pending
            and (suggestion.reviewer_id
                 == get_user_model().objects.get_system_user().id)))
    if is_system_user:
        return
    change_date = (
        suggestion.review_time
        if not suggestion.is_pending
        else suggestion.creation_time)
    update_scores.send(
        suggestion.unit.store.__class__,
        instance=suggestion.unit.store,
        users=[
            suggestion.user_id
            if suggestion.is_pending
            else suggestion.reviewer_id],
        date=localdate(change_date))


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
        instance=submission.unit.store,
        users=[submission.submitter_id],
        date=localdate(submission.creation_time))

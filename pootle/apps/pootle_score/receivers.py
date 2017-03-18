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
from pootle_statistics.models import Submission
from pootle_store.models import Store, Suggestion
from pootle_translationproject.models import TranslationProject


from .models import UserStoreScore


@receiver(update_scores, sender=get_user_model())
def update_user_scores_handler(**kwargs):
    users = kwargs.get("users")
    score_updater.get(get_user_model())(
        users=users).update()


@receiver(update_scores, sender=TranslationProject)
def update_tp_scores_handler(**kwargs):
    tp = kwargs["instance"]
    score_updater.get(tp.__class__)(tp).update(users=kwargs.get("users"))


@receiver(update_scores, sender=Store)
def update_store_scores_handler(**kwargs):
    store = kwargs["instance"]
    score_updater.get(store.__class__)(store).update(users=kwargs.get("users"))


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

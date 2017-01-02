# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db.models.signals import post_save
from django.dispatch import receiver

from pootle_statistics.models import ScoreLog, TranslationActionCodes


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
    if scorelog.action_code == TranslationActionCodes.SUGG_ADDED:
        changed["suggested"] = scorelog.wordcount
    elif scorelog.translated_wordcount is not None:
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

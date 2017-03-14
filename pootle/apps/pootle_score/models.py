# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.db import models

from .abstracts import AbstractUserScore


class UserStoreScore(AbstractUserScore):

    class Meta(AbstractUserScore.Meta):
        db_table = "pootle_user_store_score"
        unique_together = ["date", "store", "user"]

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        related_name='store_scores',
        db_index=True,
        on_delete=models.CASCADE)

    store = models.ForeignKey(
        "pootle_store.Store",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="user_scores")

    @property
    def context(self):
        return self.store


class UserTPScore(AbstractUserScore):

    class Meta(AbstractUserScore.Meta):
        db_table = "pootle_user_tp_score"
        unique_together = ["date", "tp", "user"]

    tp = models.ForeignKey(
        "pootle_translationproject.TranslationProject",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="user_scores")

    @property
    def context(self):
        return self.tp

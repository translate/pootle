# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models

from .abstracts import AbstractUserScore


class UserTPScore(AbstractUserScore):

    class Meta(AbstractUserScore.Meta):
        db_table = "pootle_user_tp_score"
        unique_together = ["date", "tp", "user"]

    def __str__(self):
        return (
            "%s(%s) %s score: %s, suggested: %s, translated: %s, reviewed: %s"
            % (self.user.username,
               self.tp.pootle_path,
               self.date,
               self.score,
               self.suggested,
               self.translated,
               self.reviewed))

    tp = models.ForeignKey(
        "pootle_translationproject.TranslationProject",
        on_delete=models.CASCADE,
        db_index=True,
        related_name="user_scores")

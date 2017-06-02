# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.db import models


class AbstractUserScore(models.Model):

    class Meta(object):
        abstract = True

    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=False,
        related_name='scores',
        db_index=True,
        on_delete=models.CASCADE)
    date = models.DateField(
        null=False,
        blank=False,
        auto_now=False,
        db_index=False)
    score = models.FloatField(
        null=False,
        blank=False,
        default=0,
        db_index=True)
    reviewed = models.IntegerField(
        null=False,
        blank=False,
        default=0,
        db_index=True)
    suggested = models.IntegerField(
        null=False,
        blank=False,
        default=0,
        db_index=True)
    translated = models.IntegerField(
        null=False,
        blank=False,
        default=0,
        db_index=True)

    def __str__(self):
        return (
            "%s(%s) %s score: %s, suggested: %s, translated: %s, reviewed: %s"
            % (self.user.username,
               self.context.pootle_path,
               self.date,
               self.score,
               self.suggested,
               self.translated,
               self.reviewed))

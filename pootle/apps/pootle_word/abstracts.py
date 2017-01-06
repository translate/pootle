# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models


class AbstractStem(models.Model):

    class Meta(object):
        abstract = True

    root = models.CharField(
        max_length=255,
        unique=True,
        null=False,
        blank=False)

    def save(self, *args, **kwargs):
        self.full_clean()
        super(AbstractStem, self).save(*args, **kwargs)

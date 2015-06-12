#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class PaidTaskTypes(object):
    TRANSLATION = 0
    REVIEW = 1
    HOURLY_WORK = 2
    CORRECTION = 3


class PaidTask(models.Model):
    """The Paid Task.

    ``task_type``, ``amount`` and ``date`` are required.
    """
    task_type = models.PositiveSmallIntegerField(
        _('Type'),
        choices=[
            (PaidTaskTypes.TRANSLATION, _('Translation')),
            (PaidTaskTypes.REVIEW, _('Review')),
            (PaidTaskTypes.HOURLY_WORK, _('Hourly Work')),
            (PaidTaskTypes.CORRECTION, _('Correction')),
        ],
        null=False,
        db_index=True,
        default=PaidTaskTypes.TRANSLATION,
    )
    amount = models.FloatField(_('Amount'), null=False, default=0)
    rate = models.FloatField(null=False, default=0)
    datetime = models.DateTimeField(_('Date'), null=False, db_index=True)
    description = models.TextField(_('Description'), null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

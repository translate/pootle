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
from django.utils import timezone
from django.utils.translation import ugettext_lazy as _


__all__ = ('PaidTask', )


class PaidTaskTypes(object):
    TRANSLATION = 0
    REVIEW = 1
    HOURLY_WORK = 2
    CORRECTION = 3


class ReportActionTypes(object):
    TRANSLATION = 0
    REVIEW = 1
    SUGGESTION = 2

    NAMES_MAP = {
        TRANSLATION: _('Translation'),
        REVIEW: _('Review'),
        SUGGESTION: _('Suggestion'),
    }


class PaidTaskManager(models.Manager):

    def for_user_in_range(self, user, start, end):
        """Returns all tasks for `user` in the [`start`, `end`] date range."""
        return self.get_queryset().filter(
            user=user,
            datetime__gte=start,
            datetime__lte=end,
        ).order_by('pk')


class PaidTask(models.Model):
    """The Paid Task.

    ``task_type``, ``amount`` and ``date`` are required.
    """

    type_choices = [
        (PaidTaskTypes.TRANSLATION, _('Translation')),
        (PaidTaskTypes.REVIEW, _('Review')),
        (PaidTaskTypes.HOURLY_WORK, _('Hourly Work')),
        (PaidTaskTypes.CORRECTION, _('Correction')),
    ]

    task_type = models.PositiveSmallIntegerField(
        _('Type'), choices=type_choices, null=False, db_index=True,
        default=PaidTaskTypes.TRANSLATION)
    amount = models.FloatField(_('Amount'), default=0, null=False)
    rate = models.FloatField(null=False, default=0)
    datetime = models.DateTimeField(_('Date'), null=False, db_index=True)
    description = models.TextField(_('Description'), null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    objects = PaidTaskManager()

    @classmethod
    def get_task_type_title(cls, task_type):
        return dict(cls.type_choices).get(task_type, '')

    def __unicode__(self):
        return (u'Task: [id=%s, user=%s, month=%s, '
                'type=%s, amount=%s, comment=%s]' %
                (self.id, self.user.username, self.datetime.strftime('%Y-%m'),
                 PaidTask.get_task_type_title(self.task_type), self.amount,
                 self.description))

    def clean(self):
        now = timezone.now()
        if settings.USE_TZ:
            now = timezone.localtime(now)
        if now.month == self.datetime.month and now.year == self.datetime.year:
            self.datetime = now

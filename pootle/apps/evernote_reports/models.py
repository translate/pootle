#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

__all__ = ('PaidTask', )

from django.conf import settings
from django.db import models
from django.utils.translation import ugettext_lazy as _


class PaidTaskTypes(object):
    TRANSLATION = 0
    REVIEW = 1
    HOURLY_WORK = 2


class PaidTask(models.Model):
    """The Paid Task.

    ``task_type``, ``amount`` and ``date`` are required.
    """
    type_choices = [
        (PaidTaskTypes.TRANSLATION, _('Translation')),
        (PaidTaskTypes.REVIEW, _('Review')),
        (PaidTaskTypes.HOURLY_WORK, _('Hourly Work')),
    ]

    task_type = models.PositiveSmallIntegerField(_('Type'), choices=type_choices,
                                                 null=False, db_index=True,
                                                 default=PaidTaskTypes.TRANSLATION)
    amount = models.PositiveIntegerField(_('Amount'), default=0, null=False)
    rate = models.FloatField(null=False, default=0)
    date = models.DateField(_('Task month'), null=False, db_index=True)
    description = models.TextField(_('Description'), null=True)
    user = models.ForeignKey(settings.AUTH_USER_MODEL)

    @classmethod
    def get_task_type_title(self, task_type):
        return dict(self.type_choices).get(task_type, '')

    def __unicode__(self):
        return u'Task: [id=%s, user=%s, type=%s, amount=%s, comment=%s, month=%s]' % \
            (self.id, self.user.username, PaidTask.get_task_type_title(self.task_type),
             self.amount, self.description, self.date.strftime('%Y-%m'))

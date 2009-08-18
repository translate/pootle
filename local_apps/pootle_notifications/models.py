#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django.db import models
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes import generic
from pootle_misc.baseurl import l

class NoticeManager(models.Manager):
    def get_notices(self, obj):
        notices = self.extra(where=['object_id = %s AND content_type_id = %s'], params=[obj.object_id, obj.content_type_id])
        return notices


class Notices(models.Model):
    content_type = models.ForeignKey(ContentType)
    object_id = models.PositiveIntegerField()
    content_object = generic.GenericForeignKey('content_type', 'object_id')
    message = models.TextField(_('message'))
    added = models.DateTimeField(_('added'), auto_now_add=True, null=True)

    objects = NoticeManager()

    def __unicode__(self):
        return self.message

    class Meta:
        ordering = ["-added"]
        verbose_name = _("notice")
        verbose_name_plural = _("notices")

    def get_absolute_url(self):
            return l("/notice/viewitem/%i/" % self.id)

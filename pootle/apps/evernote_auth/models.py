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


class EvernoteAccountManager(models.Manager):
    def get_queryset(self):
        return super(EvernoteAccountManager, self) \
            .get_queryset() \
            .select_related('user')


class EvernoteAccount(models.Model):
    evernote_id = models.IntegerField(db_index=True)
    name = models.CharField(max_length=255, db_index=True)
    email = models.EmailField()

    user = models.OneToOneField(settings.AUTH_USER_MODEL,
                                related_name='evernote_account')
    user_autocreated = models.BooleanField(default=False)

    objects = EvernoteAccountManager()

    def __unicode__(self):
        return "Name: %s; E-mail: %s;" % (self.name, self.email)

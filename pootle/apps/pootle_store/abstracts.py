# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.storage import base

from django.conf import settings
from django.db import models

from pootle.core.user import get_system_user, get_system_user_id
from .constants import UNTRANSLATED

from .fields import MultiStringField


class AbstractUnit(models.Model, base.TranslationUnit):

    store = models.ForeignKey(
        "pootle_store.Store",
        db_index=True,
        on_delete=models.CASCADE)

    index = models.IntegerField(db_index=True)
    unitid = models.TextField(editable=False)
    unitid_hash = models.CharField(max_length=32, db_index=True,
                                   editable=False)

    source_f = MultiStringField(null=True)
    source_hash = models.CharField(max_length=32, db_index=True,
                                   editable=False)
    source_wordcount = models.SmallIntegerField(default=0, editable=False)
    source_length = models.SmallIntegerField(db_index=True, default=0,
                                             editable=False)

    target_f = MultiStringField(null=True, blank=True)
    target_wordcount = models.SmallIntegerField(default=0, editable=False)
    target_length = models.SmallIntegerField(db_index=True, default=0,
                                             editable=False)

    developer_comment = models.TextField(null=True, blank=True)
    translator_comment = models.TextField(null=True, blank=True)
    locations = models.TextField(null=True, editable=False)
    context = models.TextField(null=True, editable=False)

    state = models.IntegerField(null=False, default=UNTRANSLATED,
                                db_index=True)
    revision = models.IntegerField(null=False, default=0, db_index=True,
                                   blank=True)

    # Metadata
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True,
                                         editable=False, null=True)
    mtime = models.DateTimeField(auto_now=True, db_index=True, editable=False)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        db_index=True,
        related_name='units_created',
        default=get_system_user_id,
        on_delete=models.SET(get_system_user))

    # unit translator
    submitted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        db_index=True,
        related_name='submitted',
        on_delete=models.SET(get_system_user))
    submitted_on = models.DateTimeField(db_index=True, null=True)

    commented_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        db_index=True,
        related_name='commented',
        on_delete=models.SET(get_system_user))
    commented_on = models.DateTimeField(db_index=True, null=True)

    # reviewer: who has accepted suggestion or removed FUZZY
    # None if translation has been submitted by approved translator
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        null=True,
        db_index=True,
        related_name='reviewed',
        on_delete=models.SET(get_system_user))
    reviewed_on = models.DateTimeField(db_index=True, null=True)

    class Meta(object):
        abstract = True

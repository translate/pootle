# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.db import models


class AbstractRevision(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='content type',
        related_name="content_type_set_for_%(class)s",
        on_delete=models.CASCADE)
    object_id = models.CharField(
        'object ID',
        max_length=255,
        blank=True,
        null=True)
    content_object = GenericForeignKey(
        ct_field="content_type",
        fk_field="object_id")
    key = models.CharField(
        'Revision key',
        max_length=255,
        blank=True,
        null=True,
        db_index=True)
    value = models.CharField(
        'Revision hash or numeric marker',
        max_length=255,
        default="",
        blank=False,
        null=False)

    class Meta(object):
        abstract = True
        ordering = ['pk']
        index_together = ["object_id", "content_type", "key"]
        unique_together = ["content_type", "object_id", "key"]

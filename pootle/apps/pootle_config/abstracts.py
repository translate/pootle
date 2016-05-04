# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import collections

from jsonfield.fields import JSONField

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError
from django.db import models

from .managers import ConfigManager, ConfigQuerySet


class AbstractConfig(models.Model):
    content_type = models.ForeignKey(
        ContentType,
        blank=True,
        null=True,
        db_index=True,
        verbose_name='content type',
        related_name="content_type_set_for_%(class)s",
        on_delete=models.CASCADE)
    object_pk = models.CharField(
        'object ID',
        max_length=255,
        blank=True,
        null=True)
    content_object = GenericForeignKey(
        ct_field="content_type",
        fk_field="object_pk")
    key = models.CharField(
        'Configuration key',
        max_length=255,
        blank=False,
        null=False,
        db_index=True)
    value = JSONField(
        'Configuration value',
        default="",
        blank=True,
        null=False,
        load_kwargs={'object_pairs_hook': collections.OrderedDict})

    objects = ConfigManager.from_queryset(ConfigQuerySet)()

    class Meta(object):
        abstract = True
        ordering = ['pk']
        index_together = ["content_type", "object_pk"]

    def save(self, **kwargs):
        if not self.key:
            raise ValidationError("Config object must have a key")
        if self.object_pk and not self.content_type:
            raise ValidationError(
                "Config object must have content_type when object_pk is set")
        super(AbstractConfig, self).save(**kwargs)

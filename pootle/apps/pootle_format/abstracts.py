# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models

from pootle.i18n.gettext import ugettext_lazy as _


class AbstractFileExtension(models.Model):

    class Meta(object):
        abstract = True

    def __str__(self):
        return self.name

    name = models.CharField(
        'Format filetype extension',
        max_length=15,
        unique=True,
        db_index=True)


class AbstractFormat(models.Model):

    class Meta(object):
        abstract = True
        unique_together = ["title", "extension"]

    name = models.CharField(
        _('Format name'),
        max_length=30,
        unique=True,
        db_index=True)
    title = models.CharField(
        _('Format title'),
        max_length=255,
        db_index=False)
    enabled = models.BooleanField(
        verbose_name=_('Enabled'), default=True)
    monolingual = models.BooleanField(
        verbose_name=_('Monolingual format'), default=False)

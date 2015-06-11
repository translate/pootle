#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import models
from django.utils.translation import ugettext_lazy as _

from pootle.core.markup import get_markup_filter_name, MarkupField
from pootle_app.models import Directory
from pootle_store.models import Store, Unit


class VirtualFolder(models.Model):

    name = models.CharField(_('Name'), blank=False, max_length=70)
    location = models.CharField(
        _('Location'),
        blank=False,
        max_length=255,
        help_text=_('Root path where this virtual folder is applied.'),
    )
    filter_rules = models.TextField(
        # Translators: This is a noun.
        _('Filter'),
        blank=False,
        help_text=_('Filtering rules that tell which stores this virtual '
                    'folder comprises.'),
    )
    priority = models.FloatField(
        _('Priority'),
        default=1,
        help_text=_('Number specifying importance. Greater priority means it '
                    'is more important.'),
    )
    is_public = models.BooleanField(
        _('Is public?'),
        default=True,
        help_text=_('Whether this virtual folder is public or not.'),
    )
    description = MarkupField(
        _('Description'),
        blank=True,
        help_text=_('Use this to provide more information or instructions. '
                    'Allowed markup: %s', get_markup_filter_name()),
    )
    units = models.ManyToManyField(
        Unit,
        db_index=True,
        related_name='vfolders',
    )

    class Meta:
        unique_together = ('name', 'location')


class VirtualFolderTreeItem(models.Model):

    directory = models.ForeignKey(
        Directory,
        related_name='vf_treeitems',
        db_index=True,
    )
    vfolder = models.ForeignKey(
        VirtualFolder,
        related_name='vf_treeitems',
        db_index=True,
    )
    parent = models.ForeignKey(
        'VirtualFolderTreeItem',
        related_name='child_vf_treeitems',
        null=True,
        db_index=True,
    )
    pootle_path = models.CharField(
        max_length=255,
        null=False,
        unique=True,
        db_index=True,
        editable=False,
    )
    stores = models.ManyToManyField(
        Store,
        db_index=True,
        related_name='parent_vf_treeitems',
    )

    class Meta:
        unique_together = ('directory', 'vfolder')

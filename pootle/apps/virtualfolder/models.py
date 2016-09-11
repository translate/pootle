# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from pootle.core.markup import MarkupField, get_markup_filter_display_name
from pootle.core.mixins import CachedMethods, CachedTreeItem
from pootle.core.mixins.treeitem import NoCachedStats
from pootle.core.url_helpers import (get_all_pootle_paths, get_editor_filter,
                                     split_pootle_path)
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store

from .delegate import path_matcher


class VirtualFolder(models.Model):

    # any changes to the `name` field may require updating the schema
    # see migration 0003_case_sensitive_schema.py
    name = models.CharField(
        _('Name'),
        blank=False,
        unique=True,
        max_length=70)
    title = models.CharField(
        _('Title'),
        blank=True,
        null=True,
        max_length=255)

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
                    'Allowed markup: %s', get_markup_filter_display_name()),
    )
    stores = models.ManyToManyField(
        Store,
        db_index=True,
        related_name='vfolders')
    all_projects = models.BooleanField(default=False)
    projects = models.ManyToManyField(
        Project,
        db_index=True,
        related_name='vfolders')
    all_languages = models.BooleanField(default=False)
    languages = models.ManyToManyField(
        Language,
        db_index=True,
        related_name='vfolders')

    @cached_property
    def path_matcher(self):
        return path_matcher.get(self.__class__)(self)

    def __unicode__(self):
        return self.name

    def save(self, *args, **kwargs):
        # Force validation of fields.
        self.clean_fields()

        self.name = self.name.lower()
        super(VirtualFolder, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        self.vf_treeitems.all().delete()

        super(VirtualFolder, self).delete(*args, **kwargs)

    def clean_fields(self):
        """Validate virtual folder fields."""
        if self.priority <= 0:
            raise ValidationError(u'Priority must be greater than zero.')
        if not self.filter_rules:
            raise ValidationError(u'Some filtering rule must be specified.')


class VirtualFolderTreeItemManager(models.Manager):
    use_for_related_fields = True

    def live(self):
        """Filter VirtualFolderTreeItems with non-obsolete directories."""
        return self.filter(directory__obsolete=False)


class VirtualFolderTreeItem(models.Model, CachedTreeItem):

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
    # any changes to the `pootle_path` field may require updating the schema
    # see migration 0003_case_sensitive_schema.py
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

    objects = VirtualFolderTreeItemManager()

    class Meta(object):
        unique_together = ('directory', 'vfolder')

    # # # # # # # # # # # # # #  Properties # # # # # # # # # # # # # # # # # #

    @property
    def is_visible(self):
        return (self.vfolder.is_public and
                (self.has_critical_errors or self.has_suggestions or
                 (self.vfolder.priority >= 1 and
                  not self.is_fully_translated)))

    @property
    def has_critical_errors(self):
        try:
            return self.get_error_unit_count() > 0
        except NoCachedStats:
            return False

    @property
    def has_suggestions(self):
        try:
            return self.get_cached(CachedMethods.SUGGESTIONS) > 0
        except NoCachedStats:
            return False

    @property
    def is_fully_translated(self):
        try:
            wordcount_stats = self.get_cached(CachedMethods.WORDCOUNT_STATS)
        except NoCachedStats:
            return False

        return wordcount_stats['total'] == wordcount_stats['translated']

    @property
    def code(self):
        return self.pk

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    def __unicode__(self):
        return self.pootle_path

    def save(self, *args, **kwargs):
        self.pootle_path = self.vfolder.get_adjusted_pootle_path(
            self.directory.pootle_path
        )

        # Trigger the creation of the whole parent tree up to the vfolder
        # adjusted location.
        if (self.directory.pootle_path.count('/') >
                self.vfolder.location.count('/')):
            parent = VirtualFolderTreeItem.objects.get_or_create(
                directory=self.directory.parent,
                vfolder=self.vfolder,
            )[0]
            self.parent = parent

        super(VirtualFolderTreeItem, self).save(*args, **kwargs)

        # Relate immediate child stores for this item's directory that have
        # units in this item's vfolder.
        self.stores = self.directory.child_stores.filter(
            vfolders=self.vfolder
        ).distinct()

    def delete(self, *args, **kwargs):
        self.clear_all_cache(parents=False, children=False)

        for vfolder_treeitem in self.child_vf_treeitems.iterator():
            # Store children are deleted by the regular folders.
            vfolder_treeitem.delete()

        super(VirtualFolderTreeItem, self).delete(*args, **kwargs)

    def get_translate_url(self, **kwargs):
        split_parts = list(split_pootle_path(self.pootle_path))
        parts = [self.vfolder.name] + split_parts[:2]
        parts.append(split_parts[2][len(self.vfolder.name) + 1:])
        url = reverse(
            "pootle-vfolder-tp-translate",
            args=parts)
        return u''.join(
            [url, get_editor_filter(**kwargs)])

    # # # TreeItem

    def can_be_updated(self):
        return not self.directory.obsolete

    def get_cachekey(self):
        return self.pootle_path

    def get_parents(self):
        if self.parent:
            return [self.parent]

        return []

    def get_children(self):
        result = [store for store in self.stores.live().iterator()]
        result.extend([vfolder_treeitem for vfolder_treeitem
                       in self.child_vf_treeitems.live().iterator()])
        return result

    def get_stats(self, include_children=True):
        result = super(VirtualFolderTreeItem, self).get_stats(
            include_children=include_children
        )
        result['isVisible'] = self.is_visible
        return result

    def all_pootle_paths(self):
        """Get cache_key for all parents up to virtual folder location.

        We only return the paths for the VirtualFolderTreeItem tree since we
        don't want to mess with regular CachedTreeItem stats.
        """
        return [p for p in get_all_pootle_paths(self.get_cachekey())
                if p.count('/') > self.vfolder.location.count('/')]

    # # # /TreeItem

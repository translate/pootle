#!/usr/bin/env python
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
from django.utils.translation import ugettext_lazy as _

from pootle.core.markup import MarkupField, get_markup_filter_display_name
from pootle.core.mixins import CachedMethods, CachedTreeItem
from pootle.core.mixins.treeitem import NoCachedStats
from pootle.core.url_helpers import (get_all_pootle_paths, get_editor_filter,
                                     split_pootle_path)
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_store.models import Store, Unit
from pootle_store.util import OBSOLETE

from .signals import vfolder_post_save


class VirtualFolder(models.Model):

    # any changes to the `name` field may require updating the schema
    # see migration 0003_case_sensitive_schema.py
    name = models.CharField(_('Name'), blank=False, max_length=70)

    # any changes to the `location` field may require updating the schema
    # see migration 0003_case_sensitive_schema.py
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
                    'Allowed markup: %s', get_markup_filter_display_name()),
    )
    units = models.ManyToManyField(
        Unit,
        db_index=True,
        related_name='vfolders',
    )

    class Meta(object):
        unique_together = ('name', 'location')

    @property
    def all_locations(self):
        """Return a list with all the locations this virtual folder applies.

        If the virtual folder location has no {LANG} nor {PROJ} placeholders
        then the list only contains its location. If any of the placeholders is
        present, then they get expanded to match all the existing languages and
        projects.
        """
        if "{LANG}/{PROJ}" in self.location:
            locations = []
            for lang in Language.objects.all():
                temp = self.location.replace("{LANG}", lang.code)
                for proj in Project.objects.all():
                    locations.append(temp.replace("{PROJ}", proj.code))
            return locations
        elif "{LANG}" in self.location:
            try:
                project = Project.objects.get(code=self.location.split("/")[2])
                languages = project.languages.iterator()
            except Exception:
                languages = Language.objects.iterator()

            return [self.location.replace("{LANG}", lang.code)
                    for lang in languages]
        elif "{PROJ}" in self.location:
            try:
                projects = Project.objects.filter(
                    translationproject__language__code=self.location.split("/")[1]
                ).iterator()
            except Exception:
                projects = Project.objects.iterator()

            return [self.location.replace("{PROJ}", proj.code)
                    for proj in projects]

        return [self.location]

    def __unicode__(self):
        return ": ".join([self.name, self.location])

    def save(self, *args, **kwargs):
        # Force validation of fields.
        self.clean_fields()

        self.name = self.name.lower()

        if self.pk is None:
            projects = set()
        else:
            # If this is an already existing vfolder, keep a list of the
            # projects it was related to.
            projects = set(Project.objects.filter(
                translationproject__stores__unit__vfolders=self
            ).distinct().values_list('code', flat=True))

        super(VirtualFolder, self).save(*args, **kwargs)

        # Clean any existing relationship between units and this vfolder.
        self.units.clear()

        # Recreate relationships between this vfolder and units.
        vfolder_stores_set = set()

        for location in self.all_locations:
            for filename in self.filter_rules.split(","):
                vf_file = "".join([location, filename])

                qs = Store.objects.live().filter(pootle_path=vf_file)

                if qs.exists():
                    self.units.add(*qs[0].units.all())
                    vfolder_stores_set.add(qs[0])
                else:
                    if not vf_file.endswith("/"):
                        vf_file += "/"

                    if Directory.objects.filter(pootle_path=vf_file).exists():
                        qs = Unit.objects.filter(
                            state__gt=OBSOLETE,
                            store__pootle_path__startswith=vf_file
                        )
                        self.units.add(*qs)
                        vfolder_stores_set.update(Store.objects.filter(
                            pootle_path__startswith=vf_file
                        ))

        # For each store create all VirtualFolderTreeItem tree structure up to
        # its adjusted vfolder location.
        for store in vfolder_stores_set:
            try:
                VirtualFolderTreeItem.objects.get_or_create(
                    directory=store.parent,
                    vfolder=self,
                )
            except ValidationError:
                # If there is some problem, e.g. a clash with a directory,
                # delete the virtual folder and all its related items, and
                # reraise the exception.
                self.delete()
                raise

        # Get the set of projects whose resources cache must be invalidated.
        # This includes the projects the projects it was previously related to
        # for the already existing vfolders.
        projects.update(Project.objects.filter(
            translationproject__stores__unit__vfolders=self
        ).distinct().values_list('code', flat=True))

        # Send the signal. This is used to invalidate the cached resources for
        # all the related projects.
        vfolder_post_save.send(sender=self.__class__, instance=self,
                               projects=list(projects))

    def clean_fields(self):
        """Validate virtual folder fields."""
        if not self.priority > 0:
            raise ValidationError(u'Priority must be greater than zero.')

        elif self.location == "/":
            raise ValidationError(u'The "/" location is not allowed. Use '
                                  u'"/{LANG}/{PROJ}/" instead.')
        elif self.location.startswith("/projects/"):
            raise ValidationError(u'Locations starting with "/projects/" are '
                                  u'not allowed. Use "/{LANG}/" instead.')

        if not self.filter_rules:
            raise ValidationError(u'Some filtering rule must be specified.')

    def get_adjusted_location(self, pootle_path):
        """Return the virtual folder location adjusted to the given path.

        The virtual folder location might have placeholders, which affect the
        actual filenames since those have to be concatenated to the virtual
        folder location.
        """
        count = self.location.count("/")

        if pootle_path.count("/") < count:
            raise ValueError("%s is not applicable in %s" % (self,
                                                             pootle_path))

        pootle_path_parts = pootle_path.strip("/").split("/")
        location_parts = self.location.strip("/").split("/")

        try:
            if (location_parts[0] != pootle_path_parts[0] and
                location_parts[0] != "{LANG}"):
                raise ValueError("%s is not applicable in %s" % (self,
                                                                 pootle_path))

            if (location_parts[1] != pootle_path_parts[1] and
                location_parts[1] != "{PROJ}"):
                raise ValueError("%s is not applicable in %s" % (self,
                                                                 pootle_path))
        except IndexError:
            pass

        return "/".join(pootle_path.split("/")[:count])

    def get_adjusted_pootle_path(self, pootle_path):
        """Adjust the given pootle path to this virtual folder.

        The provided pootle path is converted to a path that includes the
        virtual folder name in the right place.

        For example a virtual folder named vfolder8, with a location
        /{LANG}/firefox/browser/ in a path
        /af/firefox/browser/chrome/overrides/ gets converted to
        /af/firefox/browser/vfolder8/chrome/overrides/
        """
        count = self.location.count('/')

        if pootle_path.count('/') < count:
            # The provided pootle path is above the virtual folder location.
            path_parts = pootle_path.rstrip('/').split('/')
            pootle_path = '/'.join(path_parts +
                                   self.location.split('/')[len(path_parts):])

        if count < 3:
            # If the virtual folder location is not long as a translation
            # project pootle path then the returned adjusted location is too
            # short, meaning that the returned translate URL will have the
            # virtual folder name as the project or language code.
            path_parts = pootle_path.split('/')
            return '/'.join(path_parts[:3] + [self.name] + path_parts[3:])

        # If the virtual folder location is as long as a TP pootle path and
        # the provided pootle path isn't above the virtual folder location.
        lead = self.get_adjusted_location(pootle_path)
        trail = pootle_path.replace(lead, '').lstrip('/')
        return '/'.join([lead, self.name, trail])


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

        # Force validation of fields.
        self.clean_fields()

        # Trigger the creation of the whole parent tree up to the vfolder
        # adjusted location.
        if (self.directory.pootle_path.count('/') >
                self.vfolder.location.count('/')):
            parent, created = VirtualFolderTreeItem.objects.get_or_create(
                directory=self.directory.parent,
                vfolder=self.vfolder,
            )
            self.parent = parent

        super(VirtualFolderTreeItem, self).save(*args, **kwargs)

        # Relate immediate child stores for this item's directory that have
        # units in this item's vfolder.
        self.stores = self.directory.child_stores.filter(
            unit__vfolders=self.vfolder
        ).distinct()

    def delete(self, *args, **kwargs):
        self.clear_all_cache(parents=False, children=False)

        for vfolder_treeitem in self.child_vf_treeitems.iterator():
            # Store children are deleted by the regular folders.
            vfolder_treeitem.delete()

        super(VirtualFolderTreeItem, self).delete(*args, **kwargs)

    def clean_fields(self):
        """Validate virtual folder tree item fields."""
        if Directory.objects.filter(pootle_path=self.pootle_path).exists():
            msg = (u"Problem adding virtual folder '%s' with location '%s': "
                   u"VirtualFolderTreeItem clashes with Directory %s" %
                   (self.vfolder.name, self.vfolder.location,
                    self.pootle_path))
            raise ValidationError(msg)

    def get_translate_url(self, **kwargs):
        return u''.join([
            reverse("pootle-tp-translate",
                    args=split_pootle_path(self.pootle_path)[:-1]),
            get_editor_filter(**kwargs)])

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

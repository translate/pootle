#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

from django.core.exceptions import ValidationError
from django.db import models
from django.utils.translation import ugettext_lazy as _

from pootle.core.markup import get_markup_filter_name, MarkupField
from pootle_language.models import Language
from pootle_project.models import Project
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
    is_browsable = models.BooleanField(
        _('Is browsable?'),
        default=True,
        help_text=_('Whether this virtual folder is active or not.'),
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
        ordering = ['-priority', 'name']

    @classmethod
    def get_matching_for(cls, pootle_path):
        """Return the matching virtual folders in the given pootle path.

        Not all the applicable virtual folders have matching filtering rules.
        This method further restricts the list of applicable virtual folders to
        retrieve only those with filtering rules that actually match.
        """
        return VirtualFolder.objects.filter(
            units__store__pootle_path__startswith=pootle_path
        ).distinct()

    def __unicode__(self):
        return ": ".join([self.name, self.location])

    def save(self, *args, **kwargs):
        # Force validation of fields.
        self.clean_fields()

        self.name = self.name.lower()

        super(VirtualFolder, self).save(*args, **kwargs)

        # Clean any existing relationship between units and this vfolder.
        self.units.clear()

        # Recreate relationships between this vfolder and units.
        for location in self.get_all_pootle_paths():
            for filename in self.filter_rules.split(","):
                vf_file = "".join([location, filename])

                qs = Store.objects.filter(pootle_path=vf_file)

                if qs.exists():
                    self.units.add(*qs[0].units.all())

    def clean_fields(self):
        """Validate virtual folder fields."""
        if not self.priority > 0:
            raise ValidationError(u'Priority must be greater than zero.')

        elif self.location == "/":
            raise ValidationError(u'The "/" location is not allowed. Use '
                                  u'"/{LANG}/{PROJ}/" instead.')

    def get_all_pootle_paths(self):
        """Return a list with all the locations this virtual folder applies.

        If the virtual folder location has no {LANG} nor {PROJ} placeholders
        then the list only contains its location. If any of the placeholders is
        present, then they get expanded to match all the existing languages and
        projects.
        """
        # Locations like /project/<my_proj>/ are not handled correctly. So
        # rewrite them.
        if self.location.startswith("/projects/"):
            self.location = self.location.replace("/projects/", "/{LANG}/")

        if "{LANG}" in self.location and "{PROJ}" in self.location:
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
            except:
                languages = Language.objects.iterator()

            return [self.location.replace("{LANG}", lang.code)
                    for lang in languages]
        elif "{PROJ}" in self.location:
            try:
                projects = Project.objects.filter(
                    translationproject__language__code=self.location.split("/")[1]
                ).iterator()
            except:
                projects = Project.objects.iterator()

            return [self.location.replace("{PROJ}", proj.code)
                    for proj in projects]

        return [self.location]

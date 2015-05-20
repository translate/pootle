#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.filters.decorators import Category

from django.core.exceptions import ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils import dateformat
from django.utils.functional import cached_property
from django.utils.translation import ugettext_lazy as _

from pootle.core.markup import get_markup_filter_name, MarkupField
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_app.models import Directory
from pootle_language.models import Language
from pootle_misc.checks import get_qualitychecks_by_category
from pootle_project.models import Project
from pootle_statistics.models import Submission
from pootle_store.models import (QualityCheck, Store, Suggestion,
                                 SuggestionStates, Unit)
from pootle_store.util import (calc_total_wordcount, calc_translated_wordcount,
                               calc_fuzzy_wordcount, OBSOLETE, UNTRANSLATED)
from .signals import vfolder_post_save


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

    @property
    def tp_relative_path(self):
        """Return the virtual folder path relative to any translation project.

        This is the virtual folder location stripping out the language and
        project parts and appending the virtual folder name as if it were a
        folder.

        For example a location /af/{PROJ}/browser/ for a virtual folder default
        is returned as browser/default/
        """
        return '/'.join(self.location.strip('/').split('/')[2:] + [self.name, ''])

    @cached_property
    def code(self):
        return self.pk

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

    @classmethod
    def get_visible_for(cls, pootle_path):
        """Return the visible virtual folders in the given pootle path.

        Not all the applicable virtual folders have matching filtering rules.
        This method further restricts the list of applicable virtual folders to
        retrieve only those with filtering rules that actually match, and that
        are visible.
        """
        return cls.get_matching_for(pootle_path).filter(is_browsable=True,
                                                        priority__gte=1)

    @classmethod
    def get_stats_for(cls, pootle_path, all_vfolders=False):
        """Get stats for all the virtual folders in the given path.

        If ``all_vfolders`` is True then all virtual folders in the passed
        pootle_path are returned, independently of their priority of
        browsability.
        """
        stats = {}
        if all_vfolders:
            vfolders = cls.get_matching_for(pootle_path)
        else:
            vfolders = cls.get_visible_for(pootle_path)

        for vf in vfolders:
            units = vf.units.filter(store__pootle_path__startswith=pootle_path)
            stores = Store.objects.filter(
                pootle_path__startswith=pootle_path,
                unit__vfolders=vf
            ).distinct()

            stats[vf.code] = {
                'total': calc_total_wordcount(units),
                'translated': calc_translated_wordcount(units),
                'fuzzy': calc_fuzzy_wordcount(units),
                'suggestions': Suggestion.objects.filter(
                    unit__vfolders=vf,
                    unit__store__pootle_path__startswith=pootle_path,
                    unit__state__gt=OBSOLETE,
                    state=SuggestionStates.PENDING,
                ).count(),
                'critical': QualityCheck.objects.filter(
                    unit__vfolders=vf,
                    unit__store__pootle_path__startswith=pootle_path,
                    unit__state__gt=UNTRANSLATED,
                    category=Category.CRITICAL,
                    false_positive=False,
                ).values('unit').distinct().count(),
                'lastaction': vf.get_last_action_for(pootle_path),
                'is_dirty': any(map(lambda x: x.is_dirty(), stores)),
            }

        return stats

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
        if self.filter_rules:
            for location in self.all_locations():
                for filename in self.filter_rules.split(","):
                    vf_file = "".join([location, filename])

                    qs = Store.objects.live().filter(pootle_path=vf_file)

                    if qs.exists():
                        self.units.add(*qs[0].units.all())
                    else:
                        if not vf_file.endswith("/"):
                            vf_file += "/"

                        if Directory.objects.filter(pootle_path=vf_file).exists():
                            qs = Unit.objects.filter(
                                state__gt=OBSOLETE,
                                store__pootle_path__startswith=vf_file
                            )
                            self.units.add(*qs)

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

    def all_locations(self):
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

    def get_last_action_for(self, pootle_path):
        try:
            sub = Submission.simple_objects.filter(
                unit__vfolders=self,
                unit__store__pootle_path__startswith=pootle_path,
            ).latest()
        except Submission.DoesNotExist:
            return {'id': 0, 'mtime': 0, 'snippet': ''}

        return {
            'id': sub.unit.id,
            'mtime': int(dateformat.format(sub.creation_time, 'U')),
            'snippet': sub.get_submission_message()
        }

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

    def get_translate_url(self, pootle_path, **kwargs):
        """Get the translate URL for this virtual folder in the given path."""
        adjusted_path = self.get_adjusted_pootle_path(pootle_path)
        lang, proj, dp, fn = split_pootle_path(adjusted_path)

        return u''.join([
            reverse('pootle-tp-translate', args=[lang, proj, dp, fn]),
            get_editor_filter(**kwargs),
        ])

    def get_critical_url(self, pootle_path, **kwargs):
        critical = ','.join(get_qualitychecks_by_category(Category.CRITICAL))
        return self.get_translate_url(pootle_path, check=critical, **kwargs)


@receiver(post_save, sender=Unit)
def relate_unit(sender, instance, created=False, **kwargs):
    """Add newly created units to the virtual folders they belong, if any.

    When a new store or translation project, or even a full project is added,
    some of their units might be matched by the filters of any of the
    previously existing virtual folders, so this signal handler relates those
    new units to the virtual folders they belong to, if any.
    """
    if not created:
        return

    pootle_path = instance.store.pootle_path

    for vf in VirtualFolder.objects.iterator():
        for location in vf.all_locations():
            if not pootle_path.startswith(location):
                continue

            for filename in vf.filter_rules.split(","):
                if pootle_path == "".join([location, filename]):
                    vf.units.add(instance)
                    break

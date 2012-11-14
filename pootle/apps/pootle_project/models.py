#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

import os

from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.utils.translation import ugettext_lazy as _

from translate.filters import checks
from translate.lang.data import langcode_re

from pootle_app.lib.util import RelatedManager
from pootle_misc.aggregate import max_column
from pootle_misc.baseurl import l
from pootle_misc.util import (getfromcache, get_markup_filter_name,
                              apply_markup_filter)
from pootle_store.filetypes import (filetype_choices, factory_classes,
                                    is_monolingual)
from pootle_store.models import Unit
from pootle_store.util import absolute_real_path, statssum


class ProjectManager(RelatedManager):

    def get_by_natural_key(self, code):
        return self.get(code=code)


class Project(models.Model):

    objects = ProjectManager()

    class Meta:
        ordering = ['code']
        db_table = 'pootle_app_project'

    code_help_text = _('A short code for the project. This should only contain'
            'ASCII characters, numbers, and the underscore (_) character.')
    code = models.CharField(max_length=255, null=False, unique=True,
            db_index=True, verbose_name=_('Code'), help_text=code_help_text)

    fullname = models.CharField(max_length=255, null=False,
            verbose_name=_("Full Name"))

    description_help_text = _('A description of this project. '
            'This is useful to give more information or instructions. '
            'Allowed markup: %s', get_markup_filter_name())
    description = models.TextField(blank=True, help_text=description_help_text)
    description_html = models.TextField(editable=False, blank=True)

    checker_choices = [('standard', 'standard')]
    checkers = list(checks.projectcheckers.keys())
    checkers.sort()
    checker_choices.extend([(checker, checker) for checker in checkers])
    checkstyle = models.CharField(max_length=50, default='standard',
            null=False, choices=checker_choices,
            verbose_name=_('Quality Checks'))

    localfiletype  = models.CharField(max_length=50, default="po",
            choices=filetype_choices, verbose_name=_('File Type'))

    treestyle_choices = (
            # TODO: check that the None is stored and handled correctly
            ('auto', _('Automatic detection (slower)')),
            ('gnu', _('GNU style: files named by language code')),
            ('nongnu', _('Non-GNU: Each language in its own directory')),
    )
    treestyle = models.CharField(max_length=20, default='auto',
            choices=treestyle_choices, verbose_name=_('Project Tree Style'))

    source_language = models.ForeignKey('pootle_language.Language',
            db_index=True, verbose_name=_('Source Language'))

    ignoredfiles = models.CharField(max_length=255, blank=True, null=False,
            default="", verbose_name=_('Ignore Files'))

    directory = models.OneToOneField('pootle_app.Directory', db_index=True,
            editable=False)

    report_target_help_text = _('A URL or an email address where issues '
            'with the source text can be reported.')
    report_target = models.CharField(max_length=512, blank=True,
            verbose_name=_("Report Target"), help_text=report_target_help_text)

    def natural_key(self):
        return (self.code,)
    natural_key.dependencies = ['pootle_app.Directory']

    def __unicode__(self):
        return self.fullname

    def save(self, *args, **kwargs):
        # Create file system directory if needed
        project_path = self.get_real_path()
        if not os.path.exists(project_path):
            os.makedirs(project_path)

        from pootle_app.models.directory import Directory
        self.directory = Directory.objects.projects.get_or_make_subdir(self.code)

        # Apply markup filter
        self.description_html = apply_markup_filter(self.description)

        super(Project, self).save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        directory = self.directory

        # Just doing a plain delete will collect all related objects in memory
        # before deleting: translation projects, stores, units, quality checks,
        # pootle_store suggestions, pootle_app suggestions and submissions.
        # This can easily take down a process. If we do a translation project
        # at a time and force garbage collection, things stay much more
        # managable.
        import gc
        gc.collect()
        for tp in self.translationproject_set.iterator():
            tp.delete()
            gc.collect()

        # Here is a different version that first deletes all the related
        # objects, starting from the leaves. This will have to be maintained
        # doesn't seem to provide a real advantage in terms of performance.
        # Doing this finer grained garbage collection keeps memory usage even
        # lower but can take a bit longer.

        '''
        from pootle_statistics.models import Submission
        from pootle_app.models import Suggestion as AppSuggestion
        from pootle_store.models import Suggestion as StoreSuggestion
        from pootle_store.models import QualityCheck
        Submission.objects.filter(from_suggestion__translation_project__project=self).delete()
        AppSuggestion.objects.filter(translation_project__project=self).delete()
        StoreSuggestion.objects.filter(unit__store__translation_project__project=self).delete()
        QualityCheck.objects.filter(unit__store__translation_project__project=self).delete()
        gc.collect()
        for tp in self.translationproject_set.iterator():
            Unit.objects.filter(store__translation_project=tp).delete()
            gc.collect()
        '''

        super(Project, self).delete(*args, **kwargs)

        directory.delete()

    @getfromcache
    def get_mtime(self):
        project_units = Unit.objects.filter(
                store__translation_project__project=self
        )
        return max_column(project_units, 'mtime', None)

    @getfromcache
    def getquickstats(self):
        return statssum(self.translationproject_set.iterator())

    def translated_percentage(self):
        qs = self.getquickstats()
        max_words = max(qs['totalsourcewords'], 1)
        return int(100.0 * qs['translatedsourcewords'] / max_words)

    def _get_pootle_path(self):
        return "/projects/" + self.code + "/"
    pootle_path = property(_get_pootle_path)

    def get_real_path(self):
        return absolute_real_path(self.code)

    def get_absolute_url(self):
        return l(self.pootle_path)

    def get_template_filetype(self):
        if self.localfiletype == 'po':
            return 'pot'
        else:
            return self.localfiletype

    def get_file_class(self):
        """Returns the TranslationStore subclass required for parsing
        project files."""
        return factory_classes[self.localfiletype]

    def is_monolingual(self):
        """Returns ``True`` if this project is monolingual."""
        return is_monolingual(self.get_file_class())

    def _get_is_terminology(self):
        """Returns ``True`` if this project is a terminology project."""
        return self.checkstyle == 'terminology'
    is_terminology = property(_get_is_terminology)

    def file_belongs_to_project(self, filename, match_templates=True):
        """Tests if ``filename`` matches project filetype (ie. extension).

        If ``match_templates`` is ``True``, this will also check if the
        file matches the template filetype.
        """
        template_ext = os.path.extsep + self.get_template_filetype()
        return (filename.endswith(os.path.extsep + self.localfiletype)
                or match_templates and filename.endswith(template_ext))

    def _detect_treestyle(self):
        try:
            dirlisting = os.walk(self.get_real_path())
            dirpath, dirnames, filenames = dirlisting.next()

            if not dirnames:
                # No subdirectories
                if filter(self.file_belongs_to_project, filenames):
                    # Translation files found, assume gnu
                    return "gnu"
            else:
                # There are subdirectories
                if filter(lambda dirname: dirname == 'templates' or langcode_re.match(dirname), dirnames):
                    # Found language dirs assume nongnu
                    return "nongnu"
                else:
                    # No language subdirs found, look for any translation file
                    for dirpath, dirnames, filenames in os.walk(self.get_real_path()):
                        if filter(self.file_belongs_to_project, filenames):
                            return "gnu"
        except:
            pass

        # Unsure
        return None

    def get_treestyle(self):
        """Returns the real treestyle, if :attr:`Project.treestyle` is set
        to ``auto`` it checks the project directory and tries to guess
        if it is gnu style or nongnu style.

        We are biased towards nongnu because it makes managing projects
        from the web easier.
        """
        if self.treestyle != "auto":
            return self.treestyle
        else:
            detected = self._detect_treestyle()

            if detected is not None:
                return detected

        # When unsure return nongnu
        return "nongnu"

    def get_template_translationproject(self):
        """Returns the translation project that will be used as a template
        for this project.

        First it tries to retrieve the translation project that has the
        special 'templates' language within this project, otherwise it
        falls back to the source language set for current project.
        """
        try:
            return self.translationproject_set.get(language__code='templates')
        except ObjectDoesNotExist:
            try:
                return self.translationproject_set \
                           .get(language=self.source_language_id)
            except ObjectDoesNotExist:
                pass

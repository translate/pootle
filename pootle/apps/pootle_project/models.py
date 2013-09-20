#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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

import logging
import os

from django.conf import settings
from django.core.cache import cache
from django.core.exceptions import ObjectDoesNotExist, ValidationError
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models import Q
from django.utils.encoding import iri_to_uri
from django.utils.translation import ugettext_lazy as _

from translate.filters import checks
from translate.lang.data import langcode_re

from pootle.core.managers import RelatedManager
from pootle_app.models.permissions import PermissionSet
from pootle_misc.aggregate import max_column
from pootle_misc.baseurl import l
from pootle_misc.util import getfromcache, cached_property
from pootle_store.filetypes import filetype_choices, factory_classes
from pootle_store.models import Unit, Suggestion
from pootle_store.util import absolute_real_path, statssum, OBSOLETE


# FIXME: Generate key dynamically
CACHE_KEY = 'pootle-projects'

RESERVED_PROJECT_CODES = ('admin', 'translate', 'settings')


class ProjectManager(RelatedManager):

    def get_by_natural_key(self, code):
        return self.get(code=code)

    def cached(self):
        projects = cache.get(CACHE_KEY)
        if not projects:
            projects = self.order_by('fullname').all()
            cache.set(CACHE_KEY, projects, settings.OBJECT_CACHE_TIMEOUT)

        return projects

    def for_username(self, username):
        """Returns a list of projects available to `username`.

        Checks for `view` permissions in project directories, and if no
        explicit permissions are available, falls back to the root
        directory for that user.
        """
        key = iri_to_uri('projects:accessible:%s' % username)
        user_projects = cache.get(key, None)

        if user_projects is None:
            logging.debug(u'Cache miss for %s', key)
            lookup_args = {
                'directory__permission_sets__positive_permissions__codename':
                    'view',
                'directory__permission_sets__profile__user__username':
                    username,
            }
            user_projects = self.cached().filter(**lookup_args)

            # No explicit permissions for projects, let's examine the root
            if not user_projects.count():
                root_permissions = PermissionSet.objects.filter(
                    directory__pootle_path='/',
                    profile__user__username=username,
                    positive_permissions__codename='view',
                )
                if root_permissions.count():
                    user_projects = self.cached()

        cache.set(key, user_projects, settings.OBJECT_CACHE_TIMEOUT)

        return user_projects

    def accessible_by_user(self, user):
        """Returns a list of projects accessible by `user`.

        First checks for `user`, and if no explicit `view` permissions
        have been found, falls back to `default` (if logged-in) and
        `nobody` users.
        """
        user_projects = []

        check_usernames = ['nobody']
        if user.is_authenticated():
            check_usernames = [user.username, 'default', 'nobody']

        for username in check_usernames:
            user_projects = self.for_username(username)

            if user_projects:
                break

        return user_projects


class Project(models.Model):

    objects = ProjectManager()

    class Meta:
        ordering = ['code']
        db_table = 'pootle_app_project'

    code_help_text = _('A short code for the project. This should only contain '
            'ASCII characters, numbers, and the underscore (_) character.')
    code = models.CharField(max_length=255, null=False, unique=True,
            db_index=True, verbose_name=_('Code'), help_text=code_help_text)

    fullname = models.CharField(max_length=255, null=False,
            verbose_name=_("Full Name"))

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

    screenshot_search_prefix = models.URLField(blank=True, null=True,
            verbose_name=_('Screenshot Search Prefix'))

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
        self.directory = Directory.objects.projects \
                                          .get_or_make_subdir(self.code)

        super(Project, self).save(*args, **kwargs)

        # FIXME: far from ideal, should cache at the manager level instead
        cache.delete(CACHE_KEY)

    def get_translate_url(self, **kwargs):
        return reverse('pootle-project-translate', args=[self.code])

    def clean(self):
        if self.code in RESERVED_PROJECT_CODES:
            raise ValidationError(
                _('"%s" cannot be used as a project code' % (self.code,))
            )

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

        # FIXME: far from ideal, should cache at the manager level instead
        cache.delete(CACHE_KEY)

    @getfromcache
    def get_mtime(self):
        project_units = Unit.objects.filter(
                store__translation_project__project=self
        )
        return max_column(project_units, 'mtime', None)

    @getfromcache
    def getquickstats(self):
        return statssum(self.translationproject_set.iterator())

    @getfromcache
    def get_suggestion_count(self):
        """
        Check if any unit in the stores for the translation project in this
        project has suggestions.
        """
        criteria = {
            'unit__store__translation_project__project': self,
            'unit__state__gt': OBSOLETE,
        }
        return Suggestion.objects.filter(**criteria).count()

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

    @cached_property
    def languages(self):
        """Returns a list of active :cls:`~pootle_languages.models.Language`
        objects for this :cls:`~pootle_project.models.Project`.
        """
        from pootle_language.models import Language
        # FIXME: we should better have a way to automatically cache models with
        # built-in invalidation -- did I hear django-cache-machine?
        return Language.objects.filter(Q(translationproject__project=self),
                                       ~Q(code='templates'))

    def is_accessible_by(self, user):
        """Returns `True` if the current project is accessible by
        `user`.
        """
        return self in Project.objects.accessible_by_user(user)

    def get_template_filetype(self):
        if self.localfiletype == 'po':
            return 'pot'
        else:
            return self.localfiletype

    def get_file_class(self):
        """Returns the TranslationStore subclass required for parsing
        project files."""
        return factory_classes[self.localfiletype]

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

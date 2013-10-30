#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
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

import gettext
import logging
import os

from translate.misc.lru import LRUCachingDict
from translate.storage.base import ParseError

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models, IntegrityError
from django.db.models.signals import post_save

from pootle.core.managers import RelatedManager
from pootle.core.mixins import TreeItem
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_app.models.directory import Directory
from pootle_language.models import Language
from pootle_misc.util import cached_property, deletefromcache
from pootle_misc.checks import excluded_filters
from pootle_project.models import Project
from pootle_statistics.models import Submission
from pootle_store.models import (Store, Unit, PARSED)
from pootle_store.util import (absolute_real_path, relative_real_path,
                               OBSOLETE)


class TranslationProjectNonDBState(object):

    def __init__(self, parent):
        self.parent = parent

        # Terminology matcher
        self.termmatcher = None
        self.termmatchermtime = None


def create_translation_project(language, project):
    from pootle_app import project_tree
    if project_tree.translation_project_should_exist(language, project):
        try:
            translation_project, created = TranslationProject.objects \
                    .get_or_create(language=language, project=project)
            return translation_project
        except OSError:
            return None
        except IndexError:
            return None


def scan_translation_projects():
    for language in Language.objects.iterator():
        for project in Project.objects.iterator():
            create_translation_project(language, project)


class TranslationProjectManager(RelatedManager):
    def get_by_natural_key(self, pootle_path):
        #FIXME: should we use Language and Project codes instead?
        return self.get(pootle_path=pootle_path)

    def get_terminology_project(self, language_id):
        #FIXME: the code below currently uses the same approach to determine
        # the 'terminology' kind of a project as 'Project.is_terminology()',
        # which means it checks the value of 'checkstyle' field
        # (see pootle_project/models.py:240).
        #
        # This should probably be replaced in the future with a dedicated
        # project property.
        return self.get(language=language_id,
                        project__checkstyle='terminology')


class TranslationProject(models.Model, TreeItem):

    language = models.ForeignKey(Language, db_index=True)
    project = models.ForeignKey(Project, db_index=True)
    real_path = models.FilePathField(editable=False)
    directory = models.OneToOneField(Directory, db_index=True, editable=False)
    pootle_path = models.CharField(max_length=255, null=False, unique=True,
            db_index=True, editable=False)

    _non_db_state_cache = LRUCachingDict(settings.PARSE_POOL_SIZE,
            settings.PARSE_POOL_CULL_FREQUENCY)

    objects = TranslationProjectManager()

    class Meta:
        unique_together = ('language', 'project')
        db_table = 'pootle_app_translationproject'

    def natural_key(self):
        return (self.pootle_path,)
    natural_key.dependencies = ['pootle_app.Directory',
            'pootle_language.Language', 'pootle_project.Project']

    @cached_property
    def code(self):
        return u'-'.join([self.language.code, self.project.code])

    @property
    def name(self):
        # TODO: See if `self.fullname` can be removed
        return self.fullname

    @property
    def fullname(self):
        return "%s [%s]" % (self.project.fullname, self.language.name)

    @property
    def is_terminology_project(self):
        return self.project.checkstyle == 'terminology'

    @property
    def is_template_project(self):
        return self == self.project.get_template_translationproject()

    @property
    def abs_real_path(self):
        return absolute_real_path(self.real_path)

    @abs_real_path.setter
    def abs_real_path(self, value):
        self.real_path = relative_real_path(value)

    @property
    def file_style(self):
        return self.project.get_treestyle()

    @property
    def checker(self):
        from translate.filters import checks
        checkerclasses = [checks.projectcheckers.get(self.project.checkstyle,
                                                     checks.StandardChecker),
                          checks.StandardUnitChecker]

        return checks.TeeChecker(checkerclasses=checkerclasses,
                                 excludefilters=excluded_filters,
                                 errorhandler=self.filtererrorhandler,
                                 languagecode=self.language.code)

    @property
    def non_db_state(self):
        if not hasattr(self, "_non_db_state"):
            try:
                self._non_db_state = self._non_db_state_cache[self.id]
            except KeyError:
                self._non_db_state = TranslationProjectNonDBState(self)
                self._non_db_state_cache[self.id] = \
                        TranslationProjectNonDBState(self)

        return self._non_db_state

    @property
    def units(self):
        self.require_units()
        # FIXME: we rely on implicit ordering defined in the model. We might
        # want to consider pootle_path as well
        return Unit.objects.filter(store__translation_project=self,
                                   state__gt=OBSOLETE).select_related('store')

    def __unicode__(self):
        return self.pootle_path

    def save(self, *args, **kwargs):
        created = self.id is None

        project_dir = self.project.get_real_path()
        from pootle_app.project_tree import get_translation_project_dir
        self.abs_real_path = get_translation_project_dir(self.language,
                project_dir, self.file_style, make_dirs=True)
        self.directory = self.language.directory \
                                      .get_or_make_subdir(self.project.code)
        self.pootle_path = self.directory.pootle_path

        super(TranslationProject, self).save(*args, **kwargs)

        if created:
            self.scan_files()

    def delete(self, *args, **kwargs):
        directory = self.directory

        super(TranslationProject, self).delete(*args, **kwargs)

        directory.delete()
        deletefromcache(self, ["getquickstats", "getcompletestats",
                               "get_mtime", "get_suggestion_count"])

    def get_absolute_url(self):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)
        return reverse('pootle-tp-overview', args=[lang, proj, dir, fn])

    def get_translate_url(self, **kwargs):
        lang, proj, dir, fn = split_pootle_path(self.pootle_path)
        return u''.join([
            reverse('pootle-tp-translate', args=[lang, proj, dir, fn]),
            get_editor_filter(**kwargs),
        ])

    def filtererrorhandler(self, functionname, str1, str2, e):
        logging.error(u"Error in filter %s: %r, %r, %s", functionname, str1,
                      str2, e)
        return False

    def is_accessible_by(self, user):
        """Returns `True` if the current translation project is accessible
        by `user`.
        """
        if user.is_superuser:
            return True

        return self.project.code in Project.accessible_by_user(user)

    def update(self):
        """Update all stores to reflect state on disk"""
        stores = self.stores.exclude(file='').filter(state__gte=PARSED)
        for store in stores.iterator():
            store.update(update_translation=True,
                         update_structure=True)

    def sync(self, conservative=True, skip_missing=False, modified_since=0):
        """Sync unsaved work on all stores to disk"""
        stores = self.stores.exclude(file='').filter(state__gte=PARSED)
        for store in stores.iterator():
            store.sync(update_translation=True,
                       update_structure=not conservative,
                       conservative=conservative, create=False,
                       skip_missing=skip_missing,
                       modified_since=modified_since)

    def get_latest_submission(self):
        """Get the latest submission done in the Translation project"""
        try:
            sub = Submission.objects.filter(translation_project=self).latest()
        except Submission.DoesNotExist:
            return ''
        return sub.get_submission_message()

    def get_mtime(self):
        return self.directory.get_mtime()

    def require_units(self):
        """Makes sure all stores are parsed"""
        errors = 0
        for store in self.stores.filter(state__lt=PARSED).iterator():
            try:
                store.require_units()
            except IntegrityError:
                logging.info(u"Duplicate IDs in %s", store.abs_real_path)
                errors += 1
            except ParseError as e:
                logging.info(u"Failed to parse %s\n%s", store.abs_real_path, e)
                errors += 1
            except (IOError, OSError) as e:
                logging.info(u"Can't access %s\n%s", store.abs_real_path, e)
                errors += 1

        return errors

    ### TreeItem

    def get_children(self):
        return self.directory.get_children()

    def get_cachekey(self):
        return self.directory.pootle_path

    def get_parent(self):
        return self.directory.get_parent()

    ### /TreeItem

    def scan_files(self):
        """Scans the file system and returns a list of translation files.
        """
        projects = [p.strip() for p in self.project.ignoredfiles.split(',')]
        ignored_files = set(projects)
        ext = os.extsep + self.project.localfiletype

        # Scan for pots if template project
        if self.is_template_project:
            ext = os.extsep + self.project.get_template_filetype()

        from pootle_app.project_tree import (add_files, match_template_filename,
                                             direct_language_match_filename)

        all_files = []
        new_files = []

        if self.file_style == 'gnu':
            if self.pootle_path.startswith('/templates/'):
                file_filter = lambda filename: match_template_filename(
                                    self.project, filename,
                              )
            else:
                file_filter = lambda filename: direct_language_match_filename(
                                    self.language.code, filename,
                              )
        else:
            file_filter = lambda filename: True

        all_files, new_files = add_files(
                self,
                ignored_files,
                ext,
                self.real_path,
                self.directory,
                file_filter,
        )

        return all_files, new_files

    def initialize(self):
        try:
            from pootle.scripts import hooks
            hooks.hook(self.project.code, "initialize", self.real_path,
                    self.language.code)
        except Exception as e:
            logging.error(u"Failed to initialize (%s): %s", self.language.code,
                    e)

    ###########################################################################

    def gettermmatcher(self):
        """Returns the terminology matcher."""
        terminology_stores = Store.objects.none()
        mtime = None

        if not self.is_terminology_project:
            # Get global terminology first
            try:
                termproject = TranslationProject.objects \
                        .get_terminology_project(self.language_id)
                mtime = termproject.get_mtime()
                terminology_stores = termproject.stores.all()
            except TranslationProject.DoesNotExist:
                pass

            local_terminology = self.stores.filter(
                    name__startswith='pootle-terminology')
            for store in local_terminology.iterator():
                if mtime is None:
                    mtime = store.get_mtime()
                else:
                    mtime = max(mtime, store.get_mtime())

            terminology_stores = terminology_stores | local_terminology

        if mtime is None:
            return

        if mtime != self.non_db_state.termmatchermtime:
            from translate.search import match
            self.non_db_state.termmatcher = match.terminologymatcher(
                    terminology_stores.iterator(),
            )
            self.non_db_state.termmatchermtime = mtime

        return self.non_db_state.termmatcher

    ###########################################################################

    #FIXME: we should cache results to ease live translation
    def translate_message(self, singular, plural=None, n=1):
        for store in self.stores.iterator():
            unit = store.findunit(singular)
            if unit is not None and unit.istranslated():
                if unit.hasplural() and n != 1:
                    pluralequation = self.language.pluralequation

                    if pluralequation:
                        pluralfn = gettext.c2py(pluralequation)
                        target =  unit.target.strings[pluralfn(n)]

                        if target is not None:
                            return target
                else:
                    return unit.target

        # No translation found
        if n != 1 and plural is not None:
            return plural
        else:
            return singular


def scan_languages(sender, instance, created=False, raw=False, **kwargs):
    if not created or raw:
        return

    for language in Language.objects.iterator():
        create_translation_project(language, instance)

post_save.connect(scan_languages, sender=Project)


def scan_projects(sender, instance, created=False, raw=False, **kwargs):
    if not created or raw:
        return

    for project in Project.objects.iterator():
        create_translation_project(instance, project)

post_save.connect(scan_projects, sender=Language)

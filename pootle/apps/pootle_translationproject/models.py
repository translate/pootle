#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os

from translate.misc.lru import LRUCachingDict

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import cached_property

from pootle.core.mixins import CachedMethods, CachedTreeItem
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_app.models.directory import Directory
from pootle_app.project_tree import does_not_exist
from pootle_language.models import Language
from pootle_misc.checks import excluded_filters
from pootle_project.models import Project
from pootle_store.models import PARSED, Store, Unit
from pootle_store.util import OBSOLETE, absolute_real_path, relative_real_path
from staticpages.models import StaticPage


class TranslationProjectNonDBState(object):

    def __init__(self, parent):
        self.parent = parent

        # Terminology matcher
        self.termmatcher = None
        self.termmatchermtime = None


def create_or_resurrect_translation_project(language, project):
    tp = create_translation_project(language, project)
    if tp is not None:
        if tp.directory.obsolete:
            tp.directory.obsolete = False
            tp.directory.save()
            logging.info(u"Resurrected %s", tp)
        else:
            logging.info(u"Created %s", tp)


def create_translation_project(language, project):
    from pootle_app import project_tree
    if project_tree.translation_project_dir_exists(language, project):
        try:
            translation_project, created = TranslationProject.objects.all() \
                .get_or_create(language=language, project=project)
            return translation_project
        except OSError:
            return None
        except IndexError:
            return None


def scan_translation_projects(languages=None, projects=None):
    project_query = Project.objects.all()

    if projects is not None:
        project_query = project_query.filter(code__in=projects)

    for project in project_query.iterator():
        if does_not_exist(project.get_real_path()):
            logging.info(u"Disabling %s", project)
            project.disabled = True
            project.save()
        else:
            lang_query = Language.objects.exclude(
                id__in=project.translationproject_set.live().values_list('language',
                                                                         flat=True))
            if languages is not None:
                lang_query = lang_query.filter(code__in=languages)

            for language in lang_query.iterator():
                create_or_resurrect_translation_project(language, project)


class TranslationProjectManager(models.Manager):
    # disabled objects are hidden for related objects too
    use_for_related_fields = True

    def get_terminology_project(self, language_id):
        # FIXME: the code below currently uses the same approach to determine
        # the 'terminology' kind of a project as 'Project.is_terminology()',
        # which means it checks the value of 'checkstyle' field
        # (see pootle_project/models.py:240).
        #
        # This should probably be replaced in the future with a dedicated
        # project property.
        return self.get(language=language_id,
                        project__checkstyle='terminology')

    def live(self):
        """Filters translation projects that have non-obsolete directories."""
        return self.filter(directory__obsolete=False)

    def disabled(self):
        """Filters translation projects that belong to disabled projects."""
        return self.filter(project__disabled=True)

    def for_user(self, user, select_related=None):
        """Filters translation projects for a specific user.

        - Admins always get all translation projects.
        - Regular users only get enabled translation projects.

        :param user: The user for whom the translation projects need to be
            retrieved for.
        :return: A filtered queryset with `TranslationProject`s for `user`.
        """
        qs = self.live()
        if select_related is not None:
            qs = qs.select_related(*select_related)

        if user.is_superuser:
            return qs

        return qs.filter(project__disabled=False)

    def get_for_user(self, user, project_code, language_code,
                     select_related=None):
        """Gets a `language_code`/`project_code` translation project
        for a specific `user`.

        - Admins can get the translation project even
            if its project is disabled.
        - Regular users only get a translation project
            if its project isn't disabled.

        :param user: The user for whom the translation project needs
            to be retrieved.
        :param project_code: The code of a project for the TP to retrieve.
        :param language_code: The code of the language fro the TP to retrieve.
        :return: The `TranslationProject` matching the params, raises
            otherwise.
        """
        return self.for_user(
            user, select_related).get(
                project__code=project_code,
                language__code=language_code)


class TranslationProject(models.Model, CachedTreeItem):

    language = models.ForeignKey(Language, db_index=True)
    project = models.ForeignKey(Project, db_index=True)
    real_path = models.FilePathField(editable=False)
    directory = models.OneToOneField(Directory, db_index=True, editable=False)
    pootle_path = models.CharField(max_length=255, null=False, unique=True,
                                   db_index=True, editable=False)
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True,
                                         editable=False, null=True)

    _non_db_state_cache = LRUCachingDict(settings.PARSE_POOL_SIZE,
                                         settings.PARSE_POOL_CULL_FREQUENCY)

    objects = TranslationProjectManager()

    class Meta(object):
        unique_together = ('language', 'project')
        db_table = 'pootle_app_translationproject'

    @cached_property
    def code(self):
        return u'-'.join([self.language.code, self.project.code])

    # # # # # # # # # # # # # #  Properties # # # # # # # # # # # # # # # # # #

    @property
    def name(self):
        # TODO: See if `self.fullname` can be removed
        return self.fullname

    @property
    def fullname(self):
        return "%s [%s]" % (self.project.fullname, self.language.name)

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
        # We do not use default Translate Toolkit checkers; instead use
        # our own one
        if settings.POOTLE_QUALITY_CHECKER:
            from pootle_misc.util import import_func
            checkerclasses = [import_func(settings.POOTLE_QUALITY_CHECKER)]
        else:
            checkerclasses = [
                checks.projectcheckers.get(self.project.checkstyle,
                                           checks.StandardChecker)
            ]

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
    def disabled(self):
        return self.project.disabled

    @property
    def is_terminology_project(self):
        return self.project.checkstyle == 'terminology'

    @property
    def is_template_project(self):
        return self == self.project.get_template_translationproject()

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    def __unicode__(self):
        return self.pootle_path

    def __init__(self, *args, **kwargs):
        super(TranslationProject, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        created = self.id is None

        if created:
            from pootle_app.project_tree import translation_project_dir_exists

            template_tp = self.project.get_template_translationproject()
            initialize_from_templates = (
                not self.is_template_project
                and template_tp is not None
                and not translation_project_dir_exists(self.language,
                                                       self.project))

        self.directory = self.language.directory \
                                      .get_or_make_subdir(self.project.code)
        self.pootle_path = self.directory.pootle_path

        project_dir = self.project.get_real_path()
        from pootle_app.project_tree import get_translation_project_dir
        self.abs_real_path = get_translation_project_dir(
            self.language, project_dir, self.file_style, make_dirs=not
            self.directory.obsolete)

        super(TranslationProject, self).save(*args, **kwargs)

        if created:
            if initialize_from_templates:
                # We are adding a new TP and there are no files to import from
                # disk, so initialize the TP files using the templates TP ones.
                from pootle_app.project_tree import init_store_from_template

                template_stores = template_tp.stores.live().exclude(file="")

                for template_store in template_stores.iterator():
                    init_store_from_template(self, template_store)

            self.scan_files()

            # If this TP has no stores, cache should be updated forcibly.
            if self.stores.live().count() == 0:
                self.update_all_cache()

            # Create units from disk store
            for store in self.stores.live().iterator():
                changed = store.update_from_disk()

                # If there were changes stats will be refreshed anyway -
                # otherwise...  Trigger stats refresh for TP added from UI.
                # FIXME: This won't be necessary once #3547 is fixed.
                if not changed:
                    store.save(update_cache=True)

    def delete(self, *args, **kwargs):
        directory = self.directory

        super(TranslationProject, self).delete(*args, **kwargs)
        directory.delete()

    def get_absolute_url(self):
        return reverse(
            'pootle-tp-browse',
            args=split_pootle_path(self.pootle_path)[:-1])

    def get_translate_url(self, **kwargs):
        return u''.join(
            [reverse("pootle-tp-translate",
                     args=split_pootle_path(self.pootle_path)[:-1]),
             get_editor_filter(**kwargs)])

    def get_announcement(self, user=None):
        """Return the related announcement, if any."""
        return StaticPage.get_announcement_for(self.pootle_path, user)

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
        stores = self.stores.live().exclude(file='').filter(state__gte=PARSED)
        for store in stores.iterator():
            store.update_from_disk()

    def sync(self, conservative=True, skip_missing=False, only_newer=True):
        """Sync unsaved work on all stores to disk"""
        stores = self.stores.live().exclude(file='').filter(state__gte=PARSED)
        for store in stores.select_related("parent").iterator():
            store.sync(update_structure=not conservative,
                       conservative=conservative,
                       skip_missing=skip_missing, only_newer=only_newer)

    # # # TreeItem
    def get_children(self):
        return self.directory.children

    def get_cachekey(self):
        return self.pootle_path

    def get_parents(self):
        return [self.project]

    def clear_all_cache(self, children=True, parents=True):
        super(TranslationProject, self).clear_all_cache(children=children,
                                                        parents=parents)

        if 'virtualfolder' in settings.INSTALLED_APPS:
            # VirtualFolderTreeItem can only have VirtualFolderTreeItem parents
            # so it is necessary to flush their cache by calling them one by
            # one.
            from virtualfolder.models import VirtualFolderTreeItem
            tp_vfolder_treeitems = VirtualFolderTreeItem.objects.filter(
                pootle_path__startswith=self.pootle_path
            )
            for vfolder_treeitem in tp_vfolder_treeitems.iterator():
                vfolder_treeitem.clear_all_cache(children=False, parents=False)

    # # # /TreeItem

    def directory_exists_on_disk(self):
        """Checks if the actual directory for the translation project
        exists on disk.
        """
        return not does_not_exist(self.abs_real_path)

    def scan_files(self):
        """Scans the file system and returns a list of translation files.
        """
        projects = [p.strip() for p in self.project.ignoredfiles.split(',')]
        ignored_files = set(projects)
        ext = os.extsep + self.project.localfiletype

        # Scan for pots if template project
        if self.is_template_project:
            ext = os.extsep + self.project.get_template_filetype()

        from pootle_app.project_tree import (add_files,
                                             match_template_filename,
                                             direct_language_match_filename)

        all_files = []
        new_files = []

        if self.file_style == 'gnu':
            if self.pootle_path.startswith('/templates/'):
                file_filter = lambda filename: match_template_filename(
                    self.project, filename,)
            else:
                file_filter = lambda filename: direct_language_match_filename(
                    self.language.code, filename,)
        else:
            file_filter = lambda filename: True

        all_files, new_files, is_empty = add_files(
            self,
            ignored_files,
            ext,
            self.real_path,
            self.directory,
            file_filter,
        )

        return all_files, new_files

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
                mtime = termproject.get_cached_value(CachedMethods.MTIME)
                terminology_stores = termproject.stores.live()
            except TranslationProject.DoesNotExist:
                pass

            local_terminology = self.stores.live().filter(
                name__startswith='pootle-terminology')
            for store in local_terminology.iterator():
                if mtime is None:
                    mtime = store.get_cached_value(CachedMethods.MTIME)
                else:
                    mtime = max(mtime,
                                store.get_cached_value(CachedMethods.MTIME))

            terminology_stores = terminology_stores | local_terminology

        if mtime is None:
            return

        if mtime != self.non_db_state.termmatchermtime:
            from pootle_misc.match import Matcher
            self.non_db_state.termmatcher = Matcher(
                terminology_stores.iterator())
            self.non_db_state.termmatchermtime = mtime

        return self.non_db_state.termmatcher

    ###########################################################################


@receiver(post_save, sender=Project)
def scan_languages(sender, instance, created=False, raw=False, **kwargs):
    if not created or raw or instance.disabled:
        return

    for language in Language.objects.iterator():
        create_translation_project(language, instance)


@receiver(post_save, sender=Language)
def scan_projects(sender, instance, created=False, raw=False, **kwargs):
    if not created or raw:
        return

    for project in Project.objects.enabled().iterator():
        create_translation_project(instance, project)

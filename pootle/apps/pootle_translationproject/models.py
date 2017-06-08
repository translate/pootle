# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging

from django.contrib.contenttypes.fields import GenericRelation
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.urls import reverse
from django.utils.functional import cached_property

from pootle.core.contextmanagers import keep_data
from pootle.core.delegate import data_tool
from pootle.core.mixins import CachedTreeItem
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_app.models.directory import Directory
from pootle_app.project_tree import (does_not_exist, init_store_from_template,
                                     translation_project_dir_exists)
from pootle_checks.constants import EXCLUDED_FILTERS
from pootle_format.models import Format
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_revision.models import Revision
from pootle_store.constants import PARSED
from pootle_store.util import absolute_real_path, relative_real_path
from staticpages.models import StaticPage

from .contextmanagers import update_tp_after


logger = logging.getLogger(__name__)


def create_or_resurrect_translation_project(language, project):
    tp = create_translation_project(language, project)
    if tp is not None:
        if tp.directory.obsolete:
            tp.directory.obsolete = False
            tp.directory.save()
            logger.info(u"[update] Resurrected project: %s", tp)
        else:
            logger.info(u"[update] Created project: %s", tp)


def create_translation_project(language, project):
    if translation_project_dir_exists(language, project):
        tps = project.translationproject_set.select_related(
            "data", "directory")
        try:
            translation_project, __ = tps.get_or_create(
                language=language, project=project)
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
            project.disabled = True
            project.save()
            logger.info(u"[update] Disabled project: %s", project)
        else:
            lang_query = Language.objects.exclude(
                id__in=project.translationproject_set.live().values_list('language',
                                                                         flat=True))
            if languages is not None:
                lang_query = lang_query.filter(code__in=languages)

            for language in lang_query.iterator():
                create_or_resurrect_translation_project(language, project)


class TranslationProjectManager(models.Manager):

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

    def for_user(self, user, select_related=None):
        """Filters translation projects for a specific user.

        - Admins always get all translation projects.
        - Regular users only get enabled translation projects
            accessible to them.

        :param user: The user for whom the translation projects need to be
            retrieved for.
        :return: A filtered queryset with `TranslationProject`s for `user`.
        """
        qs = self.live()
        if select_related is not None:
            qs = qs.select_related(*select_related)

        if user.is_superuser:
            return qs

        return qs.filter(
            project__disabled=False,
            project__code__in=Project.accessible_by_user(user))

    def get_for_user(self, user, project_code, language_code,
                     select_related=None):
        """Gets a `language_code`/`project_code` translation project
        for a specific `user`.

        - Admins can get the translation project even
            if its project is disabled.
        - Regular users only get a translation project
            if its project isn't disabled and it is accessible to them.

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

    language = models.ForeignKey(
        Language, db_index=False, on_delete=models.CASCADE)
    project = models.ForeignKey(
        Project, db_index=True, on_delete=models.CASCADE)
    real_path = models.FilePathField(editable=False, null=True, blank=True)
    directory = models.OneToOneField(
        Directory, db_index=True, editable=False, on_delete=models.CASCADE)
    pootle_path = models.CharField(max_length=255, null=False, unique=True,
                                   db_index=True, editable=False)
    creation_time = models.DateTimeField(auto_now_add=True, db_index=True,
                                         editable=False, null=True)
    revisions = GenericRelation(Revision)

    objects = TranslationProjectManager()

    class Meta(object):
        unique_together = (
            ('language', 'project'),
            ('project', 'language'))
        db_table = 'pootle_app_translationproject'
        # disabled objects are hidden for related objects too
        base_manager_name = 'objects'

    @cached_property
    def code(self):
        return u'-'.join([self.language.code, self.project.code])

    @cached_property
    def data_tool(self):
        return data_tool.get(self.__class__)(self)

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
        if self.real_path is not None:
            return absolute_real_path(self.real_path)

    @abs_real_path.setter
    def abs_real_path(self, value):
        if value is not None:
            self.real_path = relative_real_path(value)
        else:
            self.real_path = None

    @property
    def file_style(self):
        return self.project.get_treestyle()

    @property
    def checker(self):
        from translate.filters import checks
        checkerclasses = [
            checks.projectcheckers.get(
                self.project.checkstyle,
                checks.StandardChecker)]
        return checks.TeeChecker(checkerclasses=checkerclasses,
                                 excludefilters=EXCLUDED_FILTERS,
                                 errorhandler=self.filtererrorhandler,
                                 languagecode=self.language.code)

    @property
    def disabled(self):
        return self.project.disabled

    @cached_property
    def templates_tp(self):
        return self.project.get_template_translationproject()

    @property
    def is_template_project(self):
        return self == self.templates_tp

    # # # # # # # # # # # # # #  Methods # # # # # # # # # # # # # # # # # # #

    def __unicode__(self):
        return self.pootle_path

    def __init__(self, *args, **kwargs):
        super(TranslationProject, self).__init__(*args, **kwargs)

    def save(self, *args, **kwargs):
        self.directory = self.language.directory \
                                      .get_or_make_subdir(self.project.code)
        self.pootle_path = self.directory.pootle_path

        if self.project.treestyle != 'pootle_fs':
            from pootle_app.project_tree import get_translation_project_dir
            self.abs_real_path = get_translation_project_dir(
                self.language, self.project, self.file_style, make_dirs=not
                self.directory.obsolete)
        else:
            self.abs_real_path = None
        super(TranslationProject, self).save(*args, **kwargs)
        if self.directory.tp_id != self.pk:
            self.directory.tp = self
            self.directory.save()

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
        logger.error(
            u"Error in filter %s: %r, %r, %s",
            functionname,
            str1,
            str2, e)
        return False

    def is_accessible_by(self, user):
        """Returns `True` if the current translation project is accessible
        by `user`.
        """
        if user.is_superuser:
            return True

        return self.project.code in Project.accessible_by_user(user)

    def can_be_inited_from_templates(self):
        """Returns `True` if the current translation project hasn't been
        saved yet and can be initialized from templates.
        """

        # This method checks if the current translation project directory
        # doesn't exist. So it won't work if the translation project is already
        # saved the database because the translation project directory is
        # auto-created in `save()` method.
        return (
            not self.is_template_project
            and self.templates_tp is not None
            and not translation_project_dir_exists(self.language,
                                                   self.project))

    def init_from_templates(self):
        """Initializes the current translation project files using
        the templates TP ones.
        """
        template_stores = self.templates_tp.stores.live().select_related(
            "filetype__template_extension",
            "filetype__extension").exclude(file="")

        for template_store in template_stores.iterator():
            init_store_from_template(self, template_store)

        self.update_from_disk()

    def update_from_disk(self, force=False, overwrite=False):
        with update_tp_after(self):
            self._update_from_disk(force=force, overwrite=overwrite)

    def _update_from_disk(self, force=False, overwrite=False):
        """Update all stores to reflect state on disk."""
        changed = []

        logger.debug(u"[update] Scanning disk: %s", self)
        # Create new, make obsolete in-DB stores to reflect state on disk
        self.scan_files()

        stores = self.stores.live().select_related(
            "parent",
            "data",
            "filetype__extension",
            "filetype__template_extension").exclude(file='')
        # Update store content from disk store
        for store in stores.iterator():
            if not store.file:
                continue
            disk_mtime = store.get_file_mtime()
            if not force and disk_mtime == store.file_mtime:
                # The file on disk wasn't changed since the last sync
                logger.debug(
                    u"File didn't change since last sync, skipping %s",
                    store.pootle_path)
                continue
            if store.updater.update_from_disk(overwrite=overwrite):
                changed.append(store)
        return changed

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

    def get_parents(self):
        return [self.project]

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

        filetypes = self.project.filetype_tool
        exts = filetypes.filetype_extensions

        # Scan for pots if template project
        if self.is_template_project:
            exts = filetypes.template_extensions

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

        all_files, new_files, __ = add_files(
            self,
            ignored_files,
            exts,
            self.real_path,
            self.directory,
            file_filter,
        )

        return all_files, new_files

    ###########################################################################


@receiver(post_save, sender=Project)
def scan_languages(**kwargs):
    instance = kwargs["instance"]
    created = kwargs.get("created", False)
    raw = kwargs.get("raw", False)

    if not created or raw or instance.disabled:
        return

    if not instance.filetypes.all().exists():
        instance.filetypes.add(Format.objects.get(name="po"))

    if instance.treestyle == 'pootle_fs':
        return

    for language in Language.objects.iterator():
        with keep_data():
            tp = create_translation_project(language, instance)
        if tp is not None:
            tp.update_from_disk()


@receiver(post_save, sender=Language)
def scan_projects(**kwargs):
    instance = kwargs["instance"]
    created = kwargs.get("created", False)
    raw = kwargs.get("raw", False)

    if not created or raw:
        return

    old_style_projects = Project.objects.enabled().exclude(
        treestyle="pootle_fs")

    for project in old_style_projects.iterator():
        with keep_data():
            tp = create_translation_project(instance, project)
        if tp is not None:
            tp.update_from_disk()

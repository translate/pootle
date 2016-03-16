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
import time

from translate.misc.lru import LRUCachingDict

from django.conf import settings
from django.core.urlresolvers import reverse
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.utils.functional import cached_property

from django_rq.queues import get_queue
from redis import WatchError
from rq.job import JobStatus, Job
from rq.utils import utcnow

from pootle.core.mixins import CachedTreeItem, CachedMethods
from pootle.core.url_helpers import get_editor_filter, split_pootle_path
from pootle_app.models.directory import Directory
from pootle_app.project_tree import does_not_exist
from pootle_language.models import Language
from pootle_misc.checks import excluded_filters
from pootle_project.models import Project
from pootle_store.models import PARSED, Store
from pootle_store.util import absolute_real_path, relative_real_path
from staticpages.models import StaticPage


class TranslationProjectNonDBState(object):

    def __init__(self, parent):
        self.parent = parent

        # Terminology matcher
        self.termmatcher = None
        self.termmatchermtime = None


def create_translation_project(language, project):
    from pootle_app import project_tree
    if project_tree.translation_project_dir_exists(language, project):
        try:
            tp, created = TranslationProject.objects \
                                            .get_or_create(language=language,
                                                           project=project)
            if created:
                logging.info(u"Created %s", tp)

            return tp
        except OSError:
            return None
        except IndexError:
            return None


def update_translation_project(language, project, **kwargs):
    try:
        tp = TranslationProject.objects.get(language=language, project=project)
        if does_not_exist(tp.abs_real_path):
            logging.info(u"Making obsolete %s", tp)
            tp.directory.makeobsolete()
            tp.update_parent_cache()
            return
        elif tp.directory.obsolete:
            tp.directory.save()
            tp.directory.obsolete = False
            logging.info(u"Resurrected %s", tp)

    except TranslationProject.DoesNotExist:
        # Create a translation project if the corresponding directory exists.
        tp = create_translation_project(language, project)

    if tp is not None:
        logging.info(u"Scanning for new files in %s", tp)
        tp.update_from_disk(**kwargs)


def sync_translation_project(language, project, **kwargs):
    try:
        instance = TranslationProject.objects.get(language=language,
                                                  project=project)
        instance.sync(**kwargs)
    except TranslationProject.DoesNotExist:
        pass


def scan_translation_projects(languages=None, projects=None, **kwargs):
    scan_disabled_projects = kwargs.get('scan_disabled_projects', False)
    overwrite = kwargs.get('overwrite', False)
    force = kwargs.get('force', False)
    wait = not kwargs.get('nowait', False)

    lang_codes = []
    prj_codes = []
    if scan_disabled_projects:
        project_query = Project.objects.all()
    else:
        project_query = Project.objects.enabled()

    if projects is not None:
        project_query = project_query.filter(code__in=projects)

    for project in project_query.iterator():
        prj_codes.append(project.code)
        if does_not_exist(project.get_real_path()):
            logging.info(u"Disabling %s", project)
            project.disabled = True
            project.save()
        else:
            lang_query = Language.objects.all()

            if languages is not None:
                lang_query = lang_query.filter(code__in=languages)

            for language in lang_query.iterator():
                logging.info(u"Add background job for (%s, %s) processing",
                             language, project)
                lang_codes.append(language.code)
                create_rq_job_wrapper(
                    language,
                    project,
                    update_translation_project,
                    force=force,
                    overwrite=overwrite)

    if wait:
        wait_for_free_translation_projects(lang_codes, prj_codes)


def sync_translation_projects(languages=None, projects=None, **kwargs):
    overwrite = kwargs.get('overwrite', False)
    skip_missing = kwargs.get('skip_missing', False)
    force = kwargs.get('force', False)
    wait = not kwargs.get('nowait', False)

    lang_codes = []
    prj_codes = []
    project_query = Project.objects.enabled()

    if projects:
        project_query = project_query.filter(code__in=projects)

    for project in project_query.iterator():
        prj_codes.append(project.code)
        lang_query = Language.objects.all()

        if languages:
            lang_query = lang_query.filter(code__in=languages)

        for language in lang_query.iterator():
            logging.info(u"Add background job for (%s, %s) processing",
                         language, project)

            lang_codes.append(language.code)
            create_rq_job_wrapper(
                language,
                project,
                sync_translation_project,
                conservative=not overwrite,
                skip_missing=skip_missing,
                only_newer=not force)

    if wait:
        wait_for_free_translation_projects(lang_codes, prj_codes)


def wait_for_free_translation_projects(lang_codes, prj_codes):
    while True:
        is_any_busy = False
        for prj_code in prj_codes:
            for lang_code in lang_codes:
                is_any_busy |= is_translation_project_busy(lang_code, prj_code)

        if not is_any_busy:
            break

        time.sleep(1)


def is_translation_project_busy(lang_code, prj_code):
        queue = get_queue()
        conn = queue.connection
        last_job_key = JobWrapper.get_last_job_key(lang_code, prj_code)
        last_job_id = conn.get(last_job_key)
        job = Job(id=last_job_id, connection=queue.connection)
        status = job.get_status()

        return (status is not None and
                status in [JobStatus.QUEUED, JobStatus.STARTED,
                           JobStatus.DEFERRED])


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

                self.update_from_disk()

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

    def update_from_disk(self, force=False, overwrite=False):
        changed = False
        # Create new, make obsolete in-DB stores to reflect state on disk
        self.scan_files()

        stores = self.stores.live().select_related('parent').exclude(file='')
        # Update store content from disk store
        for store in stores.iterator():
            if not store.file:
                continue
            disk_mtime = store.get_file_mtime()
            if not force and disk_mtime == store.file_mtime:
                # The file on disk wasn't changed since the last sync
                logging.debug(u"File didn't change since last sync, "
                              "skipping %s", store.pootle_path)
                continue

            changed = store.update_from_disk(overwrite=overwrite) or changed

        # If this TP has no stores, cache should be updated forcibly.
        if not changed and stores.count() == 0:
            self.update_all_cache()

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
    if not created or raw:
        return

    scan_translation_projects(projects=[instance.code],
                              scan_disabled_projects=instance.disabled,
                              nowait=True)


@receiver(post_save, sender=Language)
def scan_projects(sender, instance, created=False, raw=False, **kwargs):
    if not created or raw:
        return

    scan_translation_projects(languages=[instance.code], nowait=True)


class JobWrapper(object):
    """Wraps RQ Job to handle it within external `watch`,
    encapsulates work with external to RQ job params which is needed
    because of possible race conditions.
    """

    POOTLE_SYNC_LAST_JOB_PREFIX = "pootle:sync:last:job:"

    def __init__(self, id, connection):
        self.id = id
        self.func = None
        self.language = None
        self.project = None
        self.options = None
        self.depends_on = None
        self.origin = None
        self.timeout = None
        self.connection = connection
        self.job = Job(id=id, connection=self.connection)

    @classmethod
    def create(cls, func, language, project, options, connection, origin, timeout):
        """
        Creates object and initializes Job ID
        """
        job_wrapper = cls(None, connection)
        job_wrapper.job = Job(connection=connection)
        job_wrapper.id = job_wrapper.job.id
        job_wrapper.func = func
        job_wrapper.language = language
        job_wrapper.project = project
        job_wrapper.options = options
        job_wrapper.connection = connection
        job_wrapper.origin = origin
        job_wrapper.timeout = timeout

        return job_wrapper

    @classmethod
    def get_last_job_key(self, lang_code, prj_code):
        return "%s%s.%s" % (self.POOTLE_SYNC_LAST_JOB_PREFIX,
                            lang_code, prj_code)

    def create_job(self, status=None, depends_on=None):
        """Creates Job object with given job ID."""
        args = (self.language, self.project)
        self.job = Job.create(self.func, args=args, kwargs=self.options,
                              id=self.id, connection=self.connection,
                              depends_on=depends_on, status=status,
                              origin=self.origin)

        return self.job

    def save_enqueued(self, pipe):
        """Preparing job to enqueue. Works via pipeline.
        Nothing done if WatchError happens while next `pipeline.execute()`.
        """
        job = self.create_job(status=JobStatus.QUEUED)
        job.enqueued_at = utcnow()
        if job.timeout is None:
            job.timeout = self.timeout
        job.save(pipeline=pipe)

    def save_deferred(self, depends_on, pipe):
        """Preparing job to defer (add as dependent). Works via pipeline.
        Nothing done if WatchError happens while next `pipeline.execute()`.
        """
        job = self.create_job(depends_on=depends_on, status=JobStatus.DEFERRED)
        job.register_dependency(pipeline=pipe)
        job.save(pipeline=pipe)

        return job


def create_rq_job_wrapper(language, project, job_func, **options):
    queue = get_queue('default')
    if queue._async:
        create_rq_job(queue, language, project, job_func, **options)
    else:
        job_func(language, project, **options)


def create_rq_job(queue, language, project, job_func, **options):
    queue.connection.sadd(queue.redis_queues_keys, queue.key)

    job_wrapper = JobWrapper.create(job_func,
                                    language=language,
                                    project=project,
                                    options=options,
                                    connection=queue.connection,
                                    origin=queue.name,
                                    timeout=queue.DEFAULT_TIMEOUT)

    last_job_key = JobWrapper.get_last_job_key(language.code, project.code)

    with queue.connection.pipeline() as pipe:
        while True:
            try:
                pipe.watch(last_job_key)
                last_job_id = queue.connection.get(last_job_key)
                depends_on_wrapper = None
                if last_job_id is not None:
                    pipe.watch(Job.key_for(last_job_id))
                    depends_on_wrapper = JobWrapper(last_job_id, queue.connection)

                pipe.multi()

                depends_on_status = None
                if depends_on_wrapper is not None:
                    depends_on = depends_on_wrapper.job
                    depends_on_status = depends_on.get_status()

                if depends_on_status is None:
                    # Enqueue without dependencies.
                    pipe.set(last_job_key, job_wrapper.id)
                    job_wrapper.save_enqueued(pipe)
                    pipe.execute()
                    break

                pipe.set(last_job_key, job_wrapper.id)

                if depends_on_status not in [JobStatus.FINISHED, JobStatus.FAILED]:
                    # Add job as a dependent.
                    job = job_wrapper.save_deferred(last_job_id, pipe)
                    pipe.execute()
                    logging.debug('ADD AS DEPENDENT for %s (job_id=%s) OF %s',
                                  last_job_key, job.id, last_job_id)
                    return job

                job_wrapper.save_enqueued(pipe)
                pipe.execute()
                break
            except WatchError:
                logging.debug('RETRY after WatchError for %s', last_job_key)
                continue
    logging.debug('ENQUEUE %s (job_id=%s)', last_job_key, job_wrapper.id)
    queue.push_job_id(job_wrapper.id)

    return job_wrapper.job

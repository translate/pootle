# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import datetime
import logging

from django.core.management.base import BaseCommand

from pootle.runner import set_sync_mode
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


class SkipChecksMixin(object):
    def check(self, app_configs=None, tags=None, display_num_errors=False,
              include_deployment_checks=False):
        skip_tags = getattr(self, 'skip_system_check_tags', None)
        if skip_tags is not None:
            from django.core.checks.registry import registry
            tags = registry.tags_available() - set(skip_tags)

        super(SkipChecksMixin, self).check(
            app_configs=app_configs,
            tags=tags,
            display_num_errors=display_num_errors,
            include_deployment_checks=include_deployment_checks)


class PootleCommand(BaseCommand):
    """Base class for handling recursive pootle store management commands."""

    process_disabled_projects = False

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            action='append',
            dest='projects',
            help='Project to refresh',
        )
        parser.add_argument(
            '--language',
            action='append',
            dest='languages',
            help='Language to refresh',
        )
        parser.add_argument(
            "--noinput",
            action="store_true",
            default=False,
            help=u"Never prompt for input",
        )
        parser.add_argument(
            "--no-rq",
            action="store_true",
            default=False,
            help=(u"Run all jobs in a single process, without "
                  "using rq workers"),
        )

    def __init__(self, *args, **kwargs):
        self.languages = []
        self.projects = []
        super(PootleCommand, self).__init__(*args, **kwargs)

    def do_translation_project(self, tp, **options):
        process_stores = True

        if hasattr(self, "handle_translation_project"):
            logging.info(u"Running %s over %s", self.name, tp)
            try:
                process_stores = self.handle_translation_project(tp, **options)
            except Exception:
                logging.exception(u"Failed to run %s over %s", self.name, tp)
                return

            if not process_stores:
                return

        if hasattr(self, "handle_all_stores"):
            logging.info(u"Running %s over %s's files", self.name, tp)
            try:
                self.handle_all_stores(tp, **options)
            except Exception:
                logging.exception(u"Failed to run %s over %s's files",
                                  self.name, tp)
                return
        elif hasattr(self, "handle_store"):
            store_query = tp.stores.live()
            for store in store_query.iterator():
                logging.info(u"Running %s over %s",
                             self.name, store.pootle_path)
                try:
                    self.handle_store(store, **options)
                except Exception:
                    logging.exception(u"Failed to run %s over %s",
                                      self.name, store.pootle_path)

    def handle(self, **options):
        # adjust debug level to the verbosity option
        debug_levels = {
            0: logging.ERROR,
            1: logging.WARNING,
            2: logging.INFO,
            3: logging.DEBUG
        }
        logging.getLogger().setLevel(
            debug_levels.get(options['verbosity'], logging.DEBUG)
        )

        # reduce size of parse pool early on
        self.name = self.__class__.__module__.split('.')[-1]
        from pootle_store.fields import TranslationStoreFieldFile
        TranslationStoreFieldFile._store_cache.maxsize = 2
        TranslationStoreFieldFile._store_cache.cullsize = 2
        TranslationProject._non_db_state_cache.maxsize = 2
        TranslationProject._non_db_state_cache.cullsize = 2

        self.projects = options.pop('projects', [])
        self.languages = options.pop('languages', [])

        # info start
        start = datetime.datetime.now()
        logging.info('Start running of %s', self.name)

        self.handle_all(**options)

        # info finish
        end = datetime.datetime.now()
        logging.info('All done for %s in %s', self.name, end - start)

    def handle_all(self, **options):
        if options["no_rq"]:
            set_sync_mode(options['noinput'])

        if self.process_disabled_projects:
            project_query = Project.objects.all()
        else:
            project_query = Project.objects.enabled()

        if self.projects:
            project_query = project_query.filter(code__in=self.projects)

        for project in project_query.iterator():
            tp_query = project.translationproject_set.live() \
                              .order_by('language__code')

            if self.languages:
                tp_query = tp_query.filter(language__code__in=self.languages)

            for tp in tp_query.iterator():
                self.do_translation_project(tp, **options)

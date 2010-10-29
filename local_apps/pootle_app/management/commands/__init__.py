#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

import logging

from django.core.management.base import NoArgsCommand
from optparse import make_option

from pootle_translationproject.models import TranslationProject
from pootle_language.models import Language
from pootle_project.models import Project

class PootleCommand(NoArgsCommand):
    """base class for handling recursive pootle store management commands"""
    option_list = NoArgsCommand.option_list + (
        make_option('--directory', dest='directory',
                    help='directory to refresh relative to po directory'),
        make_option('--project', action='append', dest='projects',
                    help='project to refresh'),
        make_option('--language', action='append', dest='languages',
                    help='language to refresh'),
        make_option('--path-prefix', action='store', dest='path',
                    help='path prefix relative to translation project of files to refresh'),
        )

    def do_translation_project(self, tp, pootle_path, **options):
        if hasattr(self, "handle_translation_project"):
            logging.info(u"running %s over %s", self.name, tp)
            try:
                self.handle_translation_project(tp, **options)
            except Exception, e:
                logging.error(u"failed to run %s over %s:\n%s", self.name, tp, e)
                return

        if not pootle_path and hasattr(self, "handle_all_stores"):
            logging.info(u"running %s over %s's files", self.name, tp)
            try:
                self.handle_all_stores(tp, **options)
            except Exception, e:
                logging.error(u"failed to run %s over %s's files", self.name, tp)
                return
        elif hasattr(self, "handle_store"):
            store_query = tp.stores.all()
            if pootle_path:
                pootle_path = tp.pootle_path + pootle_path
                store_query = store_query.filter(pootle_path__startswith=pootle_path)
            for store in store_query.iterator():
                logging.info(u"running %s over %s", self.name, store.pootle_path)
                try:
                    self.handle_store(store, **options)
                except Exception, e:
                    logging.error(u"failed to run %s over %s:\n%s", self.name, store.pootle_path, e)

    def handle_noargs(self, **options):
        # reduce size of parse pool early on
        self.name = self.__class__.__module__.split('.')[-1]
        from pootle_store.fields import  TranslationStoreFieldFile
        TranslationStoreFieldFile._store_cache.maxsize = 2
        TranslationStoreFieldFile._store_cache.cullsize = 2
        TranslationProject._non_db_state_cache.maxsize = 2
        TranslationProject._non_db_state_cache.cullsize = 2

        directory = options.get('directory', '')
        if directory:
            languages = []
            projects = []
            path = ''
            path_parts = directory.split('/')
            if path_parts and path_parts[0]:
                projects = [path_parts[0]]
                if len(path_parts) > 1 and path_parts[1]:
                    if Language.objects.filter(code=path_parts[1]).count():
                        languages = [path_parts[1]]
                        if len(path_parts) > 2:
                            path = '/'.join(path_parts[2:])
                    else:
                        path = '/'.join(path_parts[1:])
        else:
            projects = options.get('projects', [])
            languages = options.get('languages', [])
            path = options.get('path', '')

        if languages and hasattr(self, "handle_language"):
            lang_query = Language.objects.all()
            if languages:
                lang_query = lang_query.filter(code__in=languages)
            for lang in lang_query.iterator():
                logging.info(u"running %s over %s", self.name, lang)
                try:
                    self.handle_language(lang, **options)
                except Exception, e:
                    logging.error(u"failed to run %s over %s:\n%s", self.name, lang, e)

        project_query = Project.objects.all()
        if projects:
            project_query = project_query.filter(code__in=projects)

        for project in project_query.iterator():
            if hasattr(self, "handle_project"):
                logging.info(u"running %s over %s", self.name, project)
                try:
                    self.handle_project(project, **options)
                except Exception, e:
                    logging.error(u"failed to run %s over %s:\n%s", self.name, project, e)
                    continue

            template_tp = project.get_template_translationproject()
            tp_query = project.translationproject_set.order_by('language__code')

            if languages:
                if template_tp and template_tp.language.code not in languages:
                    template_tp = None
                tp_query = tp_query.filter(language__code__in=languages)

            # update the template translation project first
            if template_tp:
                self.do_translation_project(template_tp, path, **options)

            for tp in tp_query.iterator():
                if tp == template_tp:
                    continue
                self.do_translation_project(tp, path, **options)


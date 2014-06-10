#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation
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

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'
from optparse import make_option
import logging

from pootle_app.management.commands import PootleCommand
from pootle_app.project_tree import does_not_exist
from pootle_translationproject.models import create_or_enable_translation_project
from pootle_language.models import Language
from pootle_project.models import Project


class Command(PootleCommand):
    option_list = PootleCommand.option_list + (
        make_option('--cleanup', action='store_true', dest='clean',
                    default=False, help="Delete translation projects"
                    " that ceased to exist (handle with care)."),
        )
    help = "Detects new translation projects in the file system and " \
           "adds them to database."

    def handle_project(self, project, **options):
        clean = options.get('clean', False)
        if clean and does_not_exist(project.get_real_path()):
            logging.info(u"Disabling %s", project)
            project.disabled = True
            project.save()
            project.clear_all_cache(parents=True, children=False)
            return

        lang_query = Language.objects.exclude(
                id__in=project.translationproject_set.enabled() \
                              .values_list('language', flat=True)
            )
        for language in lang_query.iterator():
            create_or_enable_translation_project(language, project)

    def handle_language(self, language, **options):
        project_query = Project.objects.exclude(
                id__in=language.translationproject_set.enabled() \
                               .values_list('project', flat=True)
            )
        for project in project_query.iterator():
            create_or_enable_translation_project(language, project)

    def handle_translation_project(self, translation_project, **options):
        clean = options.get('clean', False)
        if not translation_project.disabled and \
                clean and does_not_exist(translation_project.abs_real_path):
            logging.info(u"Disabling %s", translation_project)
            translation_project.disabled = True
            translation_project.save()
            translation_project.clear_all_cache(parents=True, children=False)

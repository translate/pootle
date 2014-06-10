#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
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

import logging

from optparse import make_option

from pootle_app.management.commands import PootleCommand
from pootle_app.project_tree import does_not_exist
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import create_or_enable_translation_project


class Command(PootleCommand):
    option_list = PootleCommand.option_list + (
        make_option('--overwrite', action='store_true', dest='overwrite',
                    default=False,
                    help="Don't just update untranslated units "
                         "and add new units, but overwrite database "
                         "translations to reflect state in files."),
        make_option('--force', action='store_true', dest='force', default=False,
                    help="Unconditionally process all files (even if they "
                         "appear unchanged)."),
        )
    help = "Update database stores from files."

    def handle_translation_project(self, translation_project, **options):
        """
        :return: flag if child stores should be updated
        """
        if (not translation_project.disabled and
            not translation_project.disable_if_missing()):
            logging.info(u"Scanning for new files in %s", translation_project)
            translation_project.scan_files()
            return True

        return False

    def handle_store(self, store, **options):
        overwrite = options.get('overwrite', False)
        force = options.get('force', False)

        store.update(overwrite=overwrite, only_newer=not force)

    def handle_all(self, **options):
        project_query = Project.objects.all()

        if self.projects:
            project_query = project_query.filter(code__in=self.projects)

        for project in project_query.iterator():
            if does_not_exist(project.get_real_path()):
                logging.info(u"Disabling %s", project)
                project.disabled = True
                project.save()
                project.clear_all_cache(parents=True, children=False)
            else:
                lang_query = Language.objects.exclude(
                        id__in=project.translationproject_set.enabled() \
                                      .values_list('language', flat=True)
                    )
                if self.languages:
                    lang_query = lang_query.filter(code__in=self.languages)

                for language in lang_query.iterator():
                    logging.info(u"Check for %s/%s", project, language)

                    create_or_enable_translation_project(language, project)

        super(Command, self).handle_all(**options)

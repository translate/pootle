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
from pootle_translationproject.models import scan_translation_projects


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
        scan_translation_projects(languages=self.languages,
                                  projects=self.projects)

        super(Command, self).handle_all(**options)

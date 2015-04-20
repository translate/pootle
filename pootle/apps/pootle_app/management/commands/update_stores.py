#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

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
        if translation_project.directory_exists():
            logging.info(u"Scanning for new files in %s", translation_project)
            translation_project.scan_files()
            return True

        translation_project.directory.makeobsolete()
        return False

    def handle_store(self, store, **options):
        overwrite = options.get('overwrite', False)
        force = options.get('force', False)

        store.update(overwrite=overwrite, only_newer=not force)

    def handle_all(self, **options):
        scan_translation_projects(languages=self.languages,
                                  projects=self.projects)

        super(Command, self).handle_all(**options)

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import PootleCommand
from pootle_translationproject.models import scan_translation_projects


class Command(PootleCommand):
    help = "Update database stores from files."
    process_disabled_projects = True

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help="Don't just update untranslated units "
                 "and add new units, but overwrite database "
                 "translations to reflect state in files.",
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Unconditionally process all files (even if they "
                 "appear unchanged).",
        )

    def handle_translation_project(self, translation_project, **options):
        """
        :return: flag if child stores should be updated
        """
        if translation_project.project.treestyle == 'pootle_fs':
            return
        if translation_project.directory_exists_on_disk():
            translation_project.update_from_disk(
                force=options['force'], overwrite=options['overwrite'])
            return False

        if translation_project.project.directory_exists_on_disk():
            translation_project.directory.makeobsolete()
        else:
            # Skip if project directory ceased to exist on disk.
            logging.warning(u"Missing project directory for %s. Skipping %s.",
                            translation_project.project, translation_project)

        return False

    def handle_store(self, store, **options):
        if not store.file:
            return
        disk_mtime = store.get_file_mtime()
        if not options["force"] and disk_mtime == store.file_mtime:
            # The file on disk wasn't changed since the last sync
            logging.debug(u"File didn't change since last sync, "
                          "skipping %s", store.pootle_path)
            return

        store.update_from_disk(overwrite=options["overwrite"])

    def handle_all(self, **options):
        scan_translation_projects(languages=self.languages,
                                  projects=self.projects)

        super(Command, self).handle_all(**options)

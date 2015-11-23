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
        make_option(
            '--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help="Don't just update untranslated units "
                 "and add new units, but overwrite database "
                 "translations to reflect state in files."),
        make_option(
            '--force',
            action='store_true',
            dest='force',
            default=False,
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
        if not store.file:
            return
        disk_mtime = store.get_file_mtime()
        if not options["force"] and disk_mtime == store.file_mtime:
            # The file on disk wasn't changed since the last sync
            logging.debug(u"File didn't change since last sync, skipping "
                          u"%s" % store.pootle_path)
            return
        if options["overwrite"]:
            store_revision = store.get_max_unit_revision()
        else:
            store_revision = store.last_sync_revision or 0

        update_revision, changes = store.update(
            store.file.store,
            store_revision=store_revision,
        )
        store.file_mtime = disk_mtime
        if changes and any(x > 0 for x in changes.values()):
            update_unsynced = None
            if store.last_sync_revision is not None:
                updated_unsynced = store.increment_unsynced_unit_revision(
                    update_revision
                )
            store.last_sync_revision = update_revision
            if update_unsynced:
                logging.info(u"[update] unsynced %d units in %s [revision: %d]"
                             % (update_unsynced, store.pootle_path,
                                update_revision))
        store.save(update_cache=False)

    def handle_all(self, **options):
        scan_translation_projects(languages=self.languages,
                                  projects=self.projects)

        super(Command, self).handle_all(**options)

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
from pootle_fs.utils import FSPlugin


logger = logging.getLogger(__name__)


class Command(PootleCommand):
    help = "Save new translations to disk manually."
    process_disabled_projects = True

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--overwrite',
            action='store_true',
            dest='overwrite',
            default=False,
            help="Don't just save translations, but "
                 "overwrite files to reflect state in database",
        )
        parser.add_argument(
            '--skip-missing',
            action='store_true',
            dest='skip_missing',
            default=False,
            help="Ignore missing files on disk",
        )
        parser.add_argument(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Don't ignore stores synced after last change",
        )

    warn_on_conflict = []

    def handle_all_stores(self, translation_project, **options):
        path_glob = "%s*" % translation_project.pootle_path
        plugin = FSPlugin(translation_project.project)
        plugin.fetch()
        if translation_project.project.pk not in self.warn_on_conflict:
            state = plugin.state()
            if any(k in state for k in ["conflict", "conflict_untracked"]):
                logger.warn(
                    "The project '%s' has conflicting changes in the database "
                    "and translation files. Use `pootle fs resolve` to tell "
                    "pootle how to merge",
                    translation_project.project.code)
                self.warn_on_conflict.append(
                    translation_project.project.pk)
        if not options["skip_missing"]:
            plugin.add(pootle_path=path_glob, update="fs")
        if options["overwrite"]:
            plugin.resolve(
                pootle_path=path_glob,
                pootle_wins=True)
        plugin.sync(pootle_path=path_glob, update="fs")
        if options["force"]:
            # touch the timestamps on disk for files that
            # werent updated
            pass

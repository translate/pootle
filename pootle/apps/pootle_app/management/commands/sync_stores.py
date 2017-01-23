# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import PootleCommand


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

    def handle_all_stores(self, translation_project, **options):
        if translation_project.project.treestyle == 'pootle_fs':
            return
        if translation_project.directory_exists_on_disk():
            translation_project.sync(
                conservative=not options['overwrite'],
                skip_missing=options['skip_missing'],
                only_newer=not options['force']
            )

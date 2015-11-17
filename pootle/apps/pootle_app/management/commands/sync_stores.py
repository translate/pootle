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
from optparse import make_option

from pootle_app.management.commands import PootleCommand

class Command(PootleCommand):
    option_list = PootleCommand.option_list + (
        make_option(
            '--skip-missing',
            action='store_true',
            dest='skip_missing',
            default=False,
            help="Ignore missing files on disk",
        ),
        make_option(
            '--force',
            action='store_true',
            dest='force',
            default=False,
            help="Don't ignore stores synced after last change",
        ),
    )
    help = "Save new translations to disk manually."

    def handle_all_stores(self, translation_project, **options):
        translation_project.sync(
                force=options['force'],
                skip_missing=options['skip_missing'],
        )

    def handle_store(self, store, **options):
        store.sync(
            force=options['force'],
            skip_missing=options['skip_missing'],
        )

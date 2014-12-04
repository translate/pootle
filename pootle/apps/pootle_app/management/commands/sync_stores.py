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
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import PootleCommand


class Command(PootleCommand):
    option_list = PootleCommand.option_list + (
        make_option('--overwrite', action='store_true', dest='overwrite',
                    default=False, help="Don't just save translations, but "
                    "overwrite files to reflect state in database"),
        make_option('--skip-missing', action='store_true', dest='skip_missing',
                    default=False, help="Ignore missing files on disk"),
        make_option('--force', action='store_true', dest='force',
                    default=False, help="Don't ignore stores synced after last change"),
        )
    help = "Save new translations to disk manually."

    def handle_all_stores(self, translation_project, **options):
        overwrite = options.get('overwrite', False)
        skip_missing = options.get('skip_missing', False)
        force = options.get('force', False)


        translation_project.sync(
                conservative=not overwrite,
                skip_missing=skip_missing,
                only_newer=not force
        )

    def handle_store(self, store, **options):
        overwrite = options.get('overwrite', False)
        skip_missing = options.get('skip_missing', False)
        force = options.get('force', False)

        store.sync(conservative=not overwrite, update_structure=overwrite,
                   skip_missing=skip_missing, only_newer=not force)

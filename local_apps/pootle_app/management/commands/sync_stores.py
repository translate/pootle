#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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

from pootle_app.management.commands import PootleCommand

class Command(PootleCommand):
    option_list = PootleCommand.option_list + (
        make_option('--overwrite', action='store_true', dest='overwrite', default=False,
                    help="don't just save translations, but overwrite files to reflect state in database"),
        )
    help = "Save new translations to disk manually."

    def handle_all_stores(self, translation_project, **options):
        overwrite = options.get('overwrite', False)
        translation_project.sync(conservative=not overwrite)

    def handle_store(self, store, **options):
        overwrite = options.get('overwrite', False)
        store.sync(update_translation=True, conservative=not overwrite, update_structure=overwrite)

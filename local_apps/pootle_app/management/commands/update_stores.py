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
import logging

from pootle_app.management.commands import PootleCommand

class Command(PootleCommand):
    option_list = PootleCommand.option_list + (
        make_option('--keep', action='store_true', dest='keep', default=False,
                    help="keep existing translations, just update untranslated units and add new units."),
        )
    help = "Update database stores from files."

    def handle_translation_project(self, translation_project, **options):
        logging.info(u"Scanning for new files in %s", translation_project)
        translation_project.scan_files()

    def handle_store(self, store, **options):
        keep = options.get('keep', False)
        # update new translations
        store.update(update_translation=not keep, conservative=keep, update_structure=True)

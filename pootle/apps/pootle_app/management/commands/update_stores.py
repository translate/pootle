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

import logging
import os
import sys
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import PootleCommand, ModifiedSinceMixin


class Command(ModifiedSinceMixin, PootleCommand):
    option_list = PootleCommand.option_list + (
        make_option('--keep', action='store_true', dest='keep', default=False,
                    help="Keep existing translations; just update "
                         "untranslated units and add new units."),
        make_option('--force', action='store_true', dest='force', default=False,
                    help="Unconditionally process all files (even if they "
                         "appear unchanged)."),
        )
    help = "Update database stores from files."

    def handle_noargs(self, **options):
        keep = options.get('keep', False)
        change_id = options.get('modified_since', 0)

        if change_id and not keep:
            logging.error(u"Both --keep and --modified-since must be set.")
            sys.exit(1)

        super(Command, self).handle_noargs(**options)

    def handle_translation_project(self, translation_project, **options):
        """
        :return: flag if child stores should be updated
        """
        if not translation_project.directory.obsolete:
            logging.info(u"Scanning for new files in %s", translation_project)
            translation_project.scan_files()
            return True

        translation_project.directory.makeobsolete()
        return False

    def handle_store(self, store, **options):
        keep = options.get('keep', False)
        force = options.get('force', False)
        change_id = options.get('modified_since', 0)

        store.update(update_translation=not keep, update_structure=True,
                     only_newer=not force, modified_since=change_id)

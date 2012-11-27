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

import logging
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'
from optparse import make_option

from pootle_app.management.commands import PootleCommand, ModifiedSinceMixin

class Command(PootleCommand, ModifiedSinceMixin):
    option_list = PootleCommand.option_list + \
                  ModifiedSinceMixin.option_modified_since + (
        make_option('--overwrite', action='store_true', dest='overwrite', default=False,
                    help="don't just save translations, but overwrite files to reflect state in database"),
        make_option('--skip-missing', action='store_true', dest='skip_missing', default=False,
                    help="ignore missing files on disk"),
        )
    help = "Save new translations to disk manually."


    def handle_noargs(self, **options):
        change_id = options.get('modified_since', 0)
        if change_id < 0:
            raise ValueError("A negative change ID is not valid.")
        from pootle_statistics.models import Submission
        latest = Submission.objects.latest()
        if change_id > latest.id:
            logging.warning("Given change ID after the latest one.")
            return

        super(Command, self).handle_noargs(**options)


    def handle_all_stores(self, translation_project, **options):
        overwrite = options.get('overwrite', False)
        skip_missing = options.get('skip_missing', False)
        change_id = options.get('modified_since', 0)
        if change_id:
            changes = translation_project.submission_set.filter(id__gte=change_id)
            if not changes.exists():
                # No change to this translation project since the given change ID
                return
        translation_project.sync(
                conservative=not overwrite,
                skip_missing=skip_missing,
                modified_since=change_id,
        )

    def handle_store(self, store, **options):
        overwrite = options.get('overwrite', False)
        skip_missing = options.get('skip_missing', False)
        store.sync(update_translation=True, conservative=not overwrite,
                   update_structure=overwrite, skip_missing=skip_missing)

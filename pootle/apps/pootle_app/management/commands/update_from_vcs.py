# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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
import logging
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_app.management.commands import PootleCommand


class Command(PootleCommand):
    help = "Allow VCS-managed data to be updated manually."

    def handle_translation_project(self, tp, **options):
        """Update all stores in a translation project from the VCS

        The translation project may be limited by language, project etc.
        """
        store_query = tp.stores.all()
        for store in store_query.iterator():
            logging.info(u"running %s over %s", self.name, store.pootle_path)
            try:
                tp.update_file_from_version_control(store)
            except Exception, e:
                logging.error(u"Failed to run %s over %s:\n%s", self.name,
                              store.pootle_path, e)

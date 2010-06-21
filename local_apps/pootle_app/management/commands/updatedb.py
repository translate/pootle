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


from django.core.management.base import NoArgsCommand

from pootle_misc import siteconfig
from pootle_misc.dbupdate import staggered_update

from pootle_misc.middleware.siteconfig import DEFAULT_BUILDVERSION
from pootle.__version__ import build as code_buildversion

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        update_db()

def update_db():
    # get current database buildversion
    config = siteconfig.load_site_config()
    db_buildversion = config.get('BUILDVERSION', DEFAULT_BUILDVERSION)
    if db_buildversion < code_buildversion:
        logging.info("Upgrading database from schema version %d to %d", db_buildversion, code_buildversion)
        for i in staggered_update(db_buildversion):
            pass
        logging.info("Database upgrade done, current schema version %d", code_buildversion)
    else:
        logging.info("No database upgrades required, current schema version %d", db_buildversion)

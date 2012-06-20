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
import sys
import os

os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import NoArgsCommand

from pootle_misc import siteconfig
from pootle_misc.middleware.siteconfig import (DEFAULT_BUILDVERSION,
                                               DEFAULT_TT_BUILDVERSION)
from pootle.__version__ import build as code_buildversion

from translate.__version__ import build as code_tt_buildversion

class Command(NoArgsCommand):
    def handle_noargs(self, **options):
        update_db()

def update_db():
    # Get current database build versions
    config = siteconfig.load_site_config()
    db_buildversion = config.get('BUILDVERSION', DEFAULT_BUILDVERSION)
    db_tt_buildversion = int(config.get('TT_BUILDVERSION', DEFAULT_TT_BUILDVERSION))

    if (db_buildversion < code_buildversion or
        db_tt_buildversion < code_tt_buildversion):

        if db_buildversion < code_buildversion:
            logging.info("Upgrading Pootle database from schema version "
                         "%d to %d", db_buildversion, code_buildversion)

        if db_tt_buildversion < code_tt_buildversion:
            logging.info("Upgrading TT database from schema version %d to %d",
                         db_tt_buildversion, code_tt_buildversion)

        from pootle_misc.dbupdate import staggered_update
        for i in staggered_update(db_buildversion, db_tt_buildversion):
            pass

        logging.info("Database upgrade done, current schema versions:\n"
                     "- Pootle: %d\n- Translate Toolkit: %d",
                     code_buildversion, code_tt_buildversion)
    else:
        logging.info("No database upgrades required, current schema "
                     "versions:\n- Pootle: %d\n- Translate Toolkit: %d",
                     db_buildversion, db_tt_buildversion)

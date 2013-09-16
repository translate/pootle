#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import logging
import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import NoArgsCommand

from pootle_app.management.commands.upgrade import DEFAULT_POOTLE_BUILDVERSION
from pootle_misc import siteconfig


class Command(NoArgsCommand):

    def handle_noargs(self, **options):
        config = siteconfig.load_site_config()
        db_buildversion = config.get('BUILDVERSION', None)

        if db_buildversion and db_buildversion < DEFAULT_POOTLE_BUILDVERSION:
            from pootle_misc.upgrade.schema import staggered_update

            logging.info('Upgrading Pootle database from schema version '
                         '%d to %d', db_buildversion,
                         DEFAULT_POOTLE_BUILDVERSION)
            staggered_update(db_buildversion)
            logging.info('Database upgrade done.')
        elif db_buildversion:
            logging.info('No database upgrades required.')

        if db_buildversion:
            new_buildversion = max(db_buildversion,
                                   DEFAULT_POOTLE_BUILDVERSION)
            logging.info('Current schema version: %d', new_buildversion)
        else:
            # Oh, the admin tried to run updatedb but there is no BUILDVERSION
            # recorded in its Pootle installation. That means it's not a legacy
            # installation.
            logging.info('Your installation is newer than Pootle 2.5.\n'
                         'You do not need to run this.')

        logging.info('THIS UPGRADE SCRIPT HAS BEEN DEPRECATED!')
        logging.info('If you are trying to upgrade Pootle from version 2.5\n'
                     'or older, please read the upgrade instructions at\n'
                     'http://docs.translatehouse.org/projects/pootle/en/'
                     'latest/server/upgrading.html')

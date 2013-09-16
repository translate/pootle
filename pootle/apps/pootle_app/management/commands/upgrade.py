#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
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
from optparse import make_option

from translate.__version__ import build as code_tt_buildversion

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import BaseCommand

from pootle.__version__ import build as code_ptl_buildversion
from pootle_misc import siteconfig


#: Build version referring to Pootle version 2.5.
#: We'll assume db represents version 2.5 if no build version is stored.
DEFAULT_POOTLE_BUILDVERSION = 22000

#: Build version referring to Translate Toolkit version 1.7.0.
#: We'll assume db represents version 1.7.0 if no build version is stored.
DEFAULT_TT_BUILDVERSION = 12005


class Command(BaseCommand):
    help = 'Runs the upgrade machinery.'

    option_list = BaseCommand.option_list + (
        make_option('--calculate-stats', action='store_true',
            dest='calculate_stats', default=False,
            help='Calculate full translation statistics after upgrading. '
                 'Default: False'),
        make_option('--flush-checks', action='store_true',
            dest='flush_qc', default=False,
            help='Flush quality checks after upgrading. Default: False'),
    )

    def handle(self, *args, **options):
        config = siteconfig.load_site_config()
        db_ptl_buildversion = config.get('POOTLE_BUILDVERSION',
                                         DEFAULT_POOTLE_BUILDVERSION)
        db_tt_buildversion = int(config.get('TT_BUILDVERSION',
                                            DEFAULT_TT_BUILDVERSION))
        ptl_changed = db_ptl_buildversion < code_ptl_buildversion
        tt_changed = db_tt_buildversion < code_tt_buildversion

        if ptl_changed or tt_changed:

            if ptl_changed:
                logging.info('Detected new Pootle version: %d.',
                             code_ptl_buildversion)
            else:
                db_ptl_buildversion = None

            if tt_changed:
                logging.info('Detected new Translate Toolkit version: %d.',
                             code_tt_buildversion)
            else:
                db_tt_buildversion = None

            logging.info('Running the upgrade machinery...')

            from pootle_misc.upgrade import run_upgrade
            run_upgrade(db_ptl_buildversion, code_ptl_buildversion,
                        db_tt_buildversion, code_tt_buildversion)

            if options['calculate_stats']:
                from pootle_misc.upgrade import calculate_stats
                calculate_stats()

            if options['flush_qc']:
                from pootle_misc.upgrade import flush_checks
                flush_checks()

            logging.info('Done.')
        else:
            logging.info(
                    'You are already up to date! Current build versions:\n'
                    '- Pootle: %s\n'
                    '- Translate Toolkit: %s',
                code_ptl_buildversion, code_tt_buildversion,
            )

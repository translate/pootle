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
from pootle_app.models.pootle_config import get_pootle_build, get_toolkit_build


#: Build version referring to Pootle version 2.5.
#: We'll assume db represents version 2.5 if no build version is stored.
DEFAULT_POOTLE_BUILDVERSION = 22000

#: Build version referring to Translate Toolkit version 1.7.0.
#: We'll assume db represents version 1.7.0 if no build version is stored.
DEFAULT_TT_BUILDVERSION = 12005


def calculate_stats():
    """Calculate full translation statistics.

    First time to visit the front page all stats for projects and
    languages will be calculated which can take forever. Since users don't
    like webpages that take forever let's precalculate the stats here.
    """
    from pootle_language.models import Language
    from pootle_project.models import Project

    logging.info('Calculating translation statistics, this will take a few '
                 'minutes')

    for language in Language.objects.iterator():
        logging.info(u'Language %s is %d%% complete', language.name,
                     language.translated_percentage())

    for project in Project.objects.iterator():
        logging.info(u'Project %s is %d%% complete', project.fullname,
                     project.translated_percentage())

    logging.info(u"Done calculating statistics")


def flush_quality_checks():
    """Revert stores to unchecked state.

    If a store has false positives marked, quality checks will be updated
    keeping false postivies intact.
    """
    from pootle_store.models import Store, QualityCheck, CHECKED, PARSED

    logging.info('Fixing quality checks. This will take a while')

    for store in Store.objects.filter(state=CHECKED).iterator():
        store_checks = QualityCheck.objects.filter(unit__store=store)
        false_positives = store_checks.filter(false_positive=True).count()

        if false_positives:
            logging.debug("%s has false positives, updating quality checks",
                          store.pootle_path)

            for unit in store.units.iterator():
                unit.update_qualitychecks(keep_false_positives=True)
        else:
            logging.debug("%s has no false positives, deleting checks",
                          store.pootle_path)
            store_checks.delete()
            store.state = PARSED
            store.save()


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
        db_ptl_buildversion = get_pootle_build(DEFAULT_POOTLE_BUILDVERSION)
        db_tt_buildversion = get_toolkit_build(DEFAULT_TT_BUILDVERSION)

        ptl_changed = db_ptl_buildversion < code_ptl_buildversion
        tt_changed = db_tt_buildversion < code_tt_buildversion

        if ptl_changed or tt_changed:

            if ptl_changed:
                logging.info('Detected new Pootle version: %d.',
                             code_ptl_buildversion)
            else:
                db_ptl_buildversion = 0

            if tt_changed:
                logging.info('Detected new Translate Toolkit version: %d.',
                             code_tt_buildversion)
            else:
                db_tt_buildversion = 0

            logging.info('Running the upgrade machinery...')

            from pootle_misc.upgrade import upgrade

            if db_ptl_buildversion and code_ptl_buildversion:
                upgrade('pootle', db_ptl_buildversion, code_ptl_buildversion)

            if db_tt_buildversion and code_tt_buildversion:
                upgrade('ttk', db_tt_buildversion, code_tt_buildversion)

            if options['calculate_stats']:
                calculate_stats()

            if options['flush_qc']:
                flush_quality_checks()

            logging.info('Done.')
        else:
            logging.info(
                    'You are already up to date! Current build versions:\n'
                    '- Pootle: %s\n'
                    '- Translate Toolkit: %s',
                code_ptl_buildversion, code_tt_buildversion,
            )

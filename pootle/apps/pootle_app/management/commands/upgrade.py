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

from translate.__version__ import build as CODE_TTK_BUILDVERSION

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import BaseCommand

from pootle.__version__ import build as CODE_PTL_BUILDVERSION
from pootle_app.models.pootle_config import get_pootle_build, get_toolkit_build


#: Build version referring to Pootle version 2.5.
#: We'll assume db represents version 2.5 if no build version is stored.
DEFAULT_POOTLE_BUILDVERSION = 22000

#: Build version referring to Translate Toolkit version 1.7.0.
#: We'll assume db represents version 1.7.0 if no build version is stored.
DEFAULT_TT_BUILDVERSION = 12005


class Command(BaseCommand):
    help = 'Runs the upgrade machinery.'

    def handle(self, *args, **options):
        db_ptl_buildversion = get_pootle_build(DEFAULT_POOTLE_BUILDVERSION)
        db_tt_buildversion = get_toolkit_build(DEFAULT_TT_BUILDVERSION)

        ptl_changed = db_ptl_buildversion < CODE_PTL_BUILDVERSION
        tt_changed = db_tt_buildversion < CODE_TTK_BUILDVERSION

        if ptl_changed or tt_changed:
            from pootle_misc.upgrade import upgrade

            if ptl_changed:
                logging.info('Detected new Pootle version: %d.',
                             CODE_PTL_BUILDVERSION)

            if tt_changed:
                logging.info('Detected new Translate Toolkit version: %d.',
                             CODE_TTK_BUILDVERSION)

            logging.info('Running the upgrade machinery...')

            if ptl_changed:
                upgrade('pootle', db_ptl_buildversion, CODE_PTL_BUILDVERSION)

            if tt_changed:
                upgrade('ttk', db_tt_buildversion, CODE_TTK_BUILDVERSION)

            # Dirty hack to drop PootleConfig and SiteConfiguration tables
            # after upgrading up to Pootle 2.6.1.
            from django.contrib.contenttypes.models import ContentType
            from django.db import connection
            from south.db import db

            ContentType.objects.filter(app_label='pootle_app', model='pootleconfig').delete()
            if u'pootle_app_pootleconfig' in connection.introspection.table_names():
                # Deleting 'PootleConfig' table.
                db.delete_table(u'pootle_app_pootleconfig')

            ContentType.objects.filter(app_label='siteconfig', model='siteconfiguration').delete()
            if u'siteconfig_siteconfiguration' in connection.introspection.table_names():
                # Deleting 'SiteConfiguration' table.
                db.delete_table(u'siteconfig_siteconfiguration')

            logging.info('Done.')
        else:
            logging.info(
                    'You are already up to date! Current build versions:\n'
                    '- Pootle: %s\n'
                    '- Translate Toolkit: %s',
                CODE_PTL_BUILDVERSION, CODE_TTK_BUILDVERSION,
            )

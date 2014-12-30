#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013, 2014 Zuza Software Foundation
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

from django.core.management import call_command
from django.core.management.base import CommandError, NoArgsCommand

from pootle.__version__ import build as NEW_POOTLE_BUILD
from pootle_app.models.pootle_config import get_pootle_build


class Command(NoArgsCommand):
    help = 'Runs the install/upgrade machinery.'

    def handle_noargs(self, **options):
        """Run the install or upgrade machinery.

        If there is an up-to-date Pootle setup then no action is performed.
        """
        current_buildversion = get_pootle_build()

        if not current_buildversion:
            logging.info('Pootle 2.6.0 is not meant to be used in real world '
                         'deployments, so please install Pootle 2.7.0 or '
                         'later instead.')
        elif current_buildversion < 21010:
            # Trying to upgrade a deployment older than Pootle 2.1.1 for which
            # we can't provide a direct upgrade.
            raise CommandError('This Pootle installation is too old. Please '
                               'upgrade first to 2.1.6 before upgrading to '
                               'this version.')
        elif current_buildversion < NEW_POOTLE_BUILD:
            logging.info('Upgrading existing Pootle installation.')

            if current_buildversion < 22000:
                # Run only if Pootle is < 2.5.0.
                call_command('updatedb')

            call_command('syncdb', interactive=False)

            if current_buildversion < 25100:
                # We are upgrading from a pre-South installation (before Pootle
                # 2.5.1), so it is necessary to fake the first migration for
                # some apps.
                OLD_APPS = ("pootle_app", "pootle_language",
                            "pootle_notifications", "pootle_project",
                            "pootle_statistics", "pootle_store",
                            "pootle_translationproject")

                if current_buildversion >= 22000:
                    # Fake the migration only if Pootle is 2.5.0.
                    OLD_APPS += ("staticpages", )

                for app in OLD_APPS:
                    call_command("migrate", app, "0001", fake=True, interactive=False)

            call_command('migrate', interactive=False)
            call_command('upgrade')

            raise CommandError('Successfully upgraded Pootle to version 2.6.0.'
                               '\n\n'
                               'Pootle 2.6.0 is not meant to be used in real '
                               'world deployments, so please proceed now with '
                               'the upgrade to Pootle 2.7.0 or later.')
        else:
            logging.info('Pootle already was up-to-date to version 2.6.0. No '
                         'action has been performed.')
            logging.info('Pootle 2.6.0 is not meant to be used in real world '
                         'deployments, so please proceed now with the upgrade '
                         'to Pootle 2.7.0 or later.')

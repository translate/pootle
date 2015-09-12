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
            raise CommandError('Pootle 2.6.1 is not meant to be used in real '
                               'world deployments.'
                               '\n\n'
                               'If you want to install a fresh Pootle then '
                               'install Pootle 2.7.0 or later.'
                               '\n\n'
                               'Otherwise you are upgrading Pootle and you '
                               'already have have upgraded up to the 2.6.1 '
                               'stage, so you must now proceed now with the '
                               'final upgrade to Pootle 2.7.0 or later.')
        elif current_buildversion < 22000:
            # Trying to upgrade a deployment older than Pootle 2.5.0 for which
            # we don't provide a direct upgrade.
            raise CommandError('This Pootle installation is too old. Please '
                               'upgrade first to 2.5.1.3 before upgrading to '
                               'this version.')
        elif current_buildversion < NEW_POOTLE_BUILD:
            logging.info('Upgrading existing Pootle installation.')

            call_command('syncdb', interactive=False)

            if current_buildversion < 25100:
                # We are upgrading from a pre-South installation (before Pootle
                # 2.5.1), so it is necessary to fake the first migration for
                # some apps.
                OLD_APPS = ("pootle_app", "pootle_language",
                            "pootle_notifications", "pootle_project",
                            "pootle_statistics", "pootle_store",
                            "pootle_translationproject", "staticpages")

                for app in OLD_APPS:
                    call_command("migrate", app, "0001", fake=True, interactive=False)

            call_command('migrate', interactive=False)
            call_command('upgrade')

            logging.warning('\n\n\n    Warning: Pootle 2.6.1 is an interim '
                            'release (a migration step to Pootle'
                            '\n             2.7.0). Do not use Pootle 2.6.1 '
                            'for any deployment.\n\n')

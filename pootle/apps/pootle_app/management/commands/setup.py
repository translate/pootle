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
            logging.info('Setting up a new Pootle installation.')

            call_command('syncdb', interactive=False)
            call_command('migrate')
            call_command('initdb')

            # Ensure we have the assets. Should be necessary only when running
            # from a checkout.
            call_command("collectstatic", clean=True, interactive=False)
            call_command("assets", "build")

            logging.info('Successfully deployed new Pootle.')
        elif current_buildversion < 25999:
            # Trying to upgrade a deployment older than Pootle 2.6.0 for which
            # we can't provide a direct upgrade.
            raise CommandError('This Pootle installation is older than 2.6.0. '
                               'Please upgrade first to 2.6.0 before '
                               'upgrading to this version.')
        elif current_buildversion < NEW_POOTLE_BUILD:
            logging.info('Upgrading existing Pootle installation.')

            call_command('syncdb', interactive=False)
            call_command('migrate')
            call_command('upgrade')

            # Ensure we don't use the old assets after upgrading.
            call_command("collectstatic", clean=True, interactive=False)
            call_command("assets", "build")

            logging.info('Successfully upgraded Pootle.')
        else:
            logging.info('Pootle already was up-to-date. No action has been '
                         'performed.')

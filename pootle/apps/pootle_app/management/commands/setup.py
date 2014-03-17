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

from __future__ import absolute_import

import logging
import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management import call_command
from django.core.management.base import CommandError, NoArgsCommand
from django.db.utils import DatabaseError

from pootle_misc.siteconfig import load_site_config
from pootle.__version__ import build as NEW_POOTLE_BUILD


class Command(NoArgsCommand):
    help = 'Runs the install/upgrade machinery.'

    def get_current_buildversion(self):
        """Retrieve the build version for the current deployment, if any."""
        try:
            config = load_site_config()
            current_buildversion = config.get('POOTLE_BUILDVERSION', None)

            if current_buildversion is None:
                # Old Pootle versions used BUILDVERSION instead.
                current_buildversion = config.get('BUILDVERSION', None)
        except DatabaseError:
            # Assume that the DatabaseError is because we have a blank database
            # from a new install, is there a better way to do this?
            current_buildversion = None

        return current_buildversion

    def handle_noargs(self, **options):
        """Run the install or upgrade machinery.

        If there is an up-to-date Pootle setup then no action is performed.
        """
        current_buildversion = self.get_current_buildversion()

        if current_buildversion is None:
            logging.info('Setting up a new Pootle installation.')

            call_command('syncdb', interactive=False)
            call_command('migrate')
            call_command('initdb')

            logging.info('Successfully deployed new Pootle.')
        elif current_buildversion < NEW_POOTLE_BUILD:
            logging.info('Upgrading existing Pootle installation.')

            if current_buildversion < 21010:
                # We are trying to upgrade a very old installation (older than
                # Pootle 2.1.1) and we can't provide a direct upgrade.
                raise CommandError('This Pootle installation is too old. '
                                   'Please upgrade first to 2.1.6 before '
                                   'upgrading to this version.')

            from .upgrade import DEFAULT_POOTLE_BUILDVERSION

            if current_buildversion < DEFAULT_POOTLE_BUILDVERSION:
                # Run only if Pootle is < 2.5.0.
                call_command('updatedb')

            call_command('syncdb', interactive=False)

            if current_buildversion < 25100:
                # We are upgrading from a pre-South installation (before Pootle
                # 2.5.1), so it is necessary to fake the first migration for
                # some apps.
                OLD_APPS = ("pootle_app", "pootle_language",
                            "pootle_notifications", "pootle_profile",
                            "pootle_project", "pootle_statistics",
                            "pootle_store", "pootle_translationproject",
                            "staticpages")
                for app in OLD_APPS:
                    call_command("migrate", app, "0001", fake=True)

            call_command('migrate')
            call_command('upgrade')

            logging.info('Successfully upgraded Pootle.')
        else:
            logging.info('Pootle already was up-to-date. No action has been '
                         'performed.')

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import BaseCommand

from pootle.core.initdb import InitDB
from . import SkipChecksMixin


class Command(SkipChecksMixin, BaseCommand):
    help = 'Populates the database with initial values: users, projects, ...'
    skip_system_check_tags = ('data', )

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-projects',
            action='store_false',
            dest='create_projects',
            default=True,
            help="Do not create the default 'terminology' and 'tutorial' "
                 "projects.",
        )

    def handle(self, **options):
        self.stdout.write('Populating the database.')
        InitDB().init_db(options["create_projects"])
        self.stdout.write('Successfully populated the database.')
        self.stdout.write("To create an admin user, use the `pootle "
                          "createsuperuser` command.")

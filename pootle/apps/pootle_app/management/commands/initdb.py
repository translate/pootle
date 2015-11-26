#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from optparse import make_option
import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import NoArgsCommand

from pootle.core.initdb import initdb


class Command(NoArgsCommand):
    help = 'Populates the database with initial values: users, projects, ...'

    option_list = NoArgsCommand.option_list + (
        make_option(
            '--no-projects',
            action='store_false',
            dest='create_projects',
            default=True,
            help="Do not create the default 'terminology' and 'tutorial'"
                 "projects.",
        ), )

    def handle_noargs(self, **options):
        self.stdout.write('Populating the database.')
        initdb(options["create_projects"])
        self.stdout.write('Successfully populated the database.')
        self.stdout.write("To create an admin user, use the `pootle "
                          "createsuperuser` command.")

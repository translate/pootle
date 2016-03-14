#!/usr/bin/env python
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


class Command(BaseCommand):
    help = 'Populates the database with initial values: users, projects, ...'

    def add_arguments(self, parser):
        parser.add_argument(
            '--no-projects',
            action='store_false',
            dest='create_projects',
            default=True,
            help="Do not create the default 'terminology' and 'tutorial' "
                 "projects.",
        )

    def check(self, app_configs=None, tags=None, display_num_errors=False,
              include_deployment_checks=False):
        from django.core.checks.registry import registry

        tags = registry.tags_available()
        tags.remove('data')
        super(Command, self).check(
            app_configs=app_configs,
            tags=tags,
            display_num_errors=display_num_errors,
            include_deployment_checks=include_deployment_checks)

    def handle(self, **options):
        self.stdout.write('Populating the database.')
        InitDB().init_db(options["create_projects"])
        self.stdout.write('Successfully populated the database.')
        self.stdout.write("To create an admin user, use the `pootle "
                          "createsuperuser` command.")

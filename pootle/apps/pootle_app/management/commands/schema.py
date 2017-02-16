# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import BaseCommand, CommandError

from pootle.core.schema.base import SchemaTool


class Command(BaseCommand):
    help = "Print Pootle's current schema state."
    requires_system_checks = False

    def add_arguments(self, parser):
        parser.add_argument(
            'args',
            metavar='app_label',
            nargs='*',
            help='Application labels.'
        )
        check_or_dump = parser.add_mutually_exclusive_group()
        check_or_dump.add_argument(
            '--check',
            action='store_true',
            default=False,
            dest='check',
            help='',
        )
        check_or_dump.add_argument(
            '--dump',
            action='store_true',
            default=False,
            dest='dump',
            help='',
        )

    def handle(self, *app_labels, **options):
        try:
            schema_tool = SchemaTool(*app_labels)
        except (LookupError, ImportError) as e:
            raise CommandError("%s. Are you sure your INSTALLED_APPS setting is correct?" % e)

        if options['check']:
            self.stdout.write('%s' % schema_tool.state)
        if options['dump']:
            self.stdout.write('Schema defaults:\n%s' %
                schema_tool.schema_dumper.get_defaults())
            for table in schema_tool.get_tables():
                self.stdout.write(
                    'Table fields %s:\n%s' % (
                        table,
                        schema_tool.schema_dumper.get_table_fields(table),
                    )
                )
                self.stdout.write(
                    'Table indices %s:\n%s' % (
                        table,
                        schema_tool.schema_dumper.get_table_indices(table),
                    )
                )
                self.stdout.write(
                    'Table constraints %s:\n%s' % (
                        table,
                        schema_tool.schema_dumper.get_table_constraints(table),
                    )
                )

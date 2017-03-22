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

from pootle.core.schema.base import SchemaTool, UnsupportedDBError
from pootle.core.schema.dump import (SchemaAppDump, SchemaDump,
                                     SchemaTableDump)


class SchemaCommand(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            '--fields',
            action='store_true',
            default=False,
            help='Table fields.',
        )
        parser.add_argument(
            '--indices',
            action='store_true',
            default=False,
            help='Table indices.',
        )
        parser.add_argument(
            '--constraints',
            action='store_true',
            default=False,
            help='Table constraints.',
        )
        super(SchemaCommand, self).add_arguments(parser)

    def handle_table(self, table_name, **options):
        result = SchemaTableDump(table_name)
        all_options = (
            not options['fields']
            and not options['indices']
            and not options['constraints']
        )
        if options['fields'] or all_options:
            result.load({
                'fields': self.schema_tool.get_table_fields(table_name)})
        if options['indices'] or all_options:
            result.load({
                'indices': self.schema_tool.get_table_indices(table_name)})
        if options['constraints'] or all_options:
            result.load({
                'constraints':
                    self.schema_tool.get_table_constraints(table_name)})

        return result


class SchemaTableCommand(SchemaCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'args',
            metavar='table_name',
            nargs='+',
            help='Table names.'
        )
        super(SchemaTableCommand, self).add_arguments(parser)

    def handle(self, *args, **options):
        try:
            self.schema_tool = SchemaTool()
        except UnsupportedDBError as e:
            raise CommandError(e)

        all_tables = self.schema_tool.get_tables()
        if not set(args).issubset(set(all_tables)):
            raise CommandError("Unrecognized tables: %s" %
                               list(set(args) - set(all_tables)))

        result = SchemaDump()
        for table_name in args:
            app_label = self.schema_tool.get_app_by_table(table_name)
            if not result.app_exists(app_label):
                app_result = SchemaAppDump(app_label)
                result.add_app(app_result)
            else:
                app_result = result.get_app(app_label)
            app_result.add_table(
                self.handle_table(table_name, **options))

        self.stdout.write(str(result))


class SchemaAppCommand(SchemaCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            'args',
            metavar='app_label',
            nargs='+',
            help='Application labels.'
        )
        parser.add_argument(
            '--tables',
            action='store_true',
            default=False,
            dest='tables',
            help='Print all table names.',
        )
        super(SchemaAppCommand, self).add_arguments(parser)

    def handle(self, *args, **options):
        try:
            self.schema_tool = SchemaTool(*args)
        except (LookupError, ImportError) as e:
            raise CommandError("%s. Are you sure your INSTALLED_APPS "
                               "setting is correct?" % e)
        except UnsupportedDBError as e:
            raise CommandError(e)

        if options['tables']:
            result = SchemaDump()
            for app_label in args:
                result.set_table_list(
                    self.schema_tool.get_app_tables(app_label))

            self.stdout.write(str(result))
        else:
            result = SchemaDump()
            for app_label in args:
                app_result = SchemaAppDump(app_label)
                for table_name in self.schema_tool.get_app_tables(app_label):
                    app_result.add_table(
                        self.handle_table(table_name, **options))
                result.add_app(app_result)

            self.stdout.write(str(result))

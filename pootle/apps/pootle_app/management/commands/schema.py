# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import CommandError

from pootle.core.management.subcommands import CommandWithSubcommands
from pootle.core.schema.base import SchemaTool, UnsupportedDBError
from pootle.core.schema.dump import (SchemaAppDump, SchemaDump,
                                     SchemaTableDump)

from .schema_commands import SchemaAppCommand, SchemaTableCommand


class Command(CommandWithSubcommands):
    help = "Pootle schema state command."
    requires_system_checks = False

    subcommands = {
        "app": SchemaAppCommand,
        "table": SchemaTableCommand,
    }

    def add_arguments(self, parser):

        dump_or_tables = parser.add_mutually_exclusive_group()
        dump_or_tables.add_argument(
            '--dump',
            action='store_true',
            default=False,
            dest='dump',
            help='Print schema settings.',
        )
        dump_or_tables.add_argument(
            '--tables',
            action='store_true',
            default=False,
            dest='tables',
            help='Print all table names.',
        )
        super(Command, self).add_arguments(parser)

    def handle(self, **options):
        try:
            schema_tool = SchemaTool()
        except UnsupportedDBError as e:
            raise CommandError(e)

        result = SchemaDump()
        if options['tables']:
            result.set_table_list(schema_tool.get_tables())
            self.stdout.write(str(result))
        else:
            result.load({
                'defaults': schema_tool.get_defaults()})
            for app_label in schema_tool.app_configs:
                app_dump = SchemaAppDump(app_label)
                table_names = schema_tool.get_app_tables(app_label)
                for table_name in table_names:
                    table_dump = SchemaTableDump(table_name)
                    table_dump.load({
                        'fields': schema_tool.get_table_fields(table_name),
                        'indices': schema_tool.get_table_indices(table_name),
                        'constraints':
                            schema_tool.get_table_constraints(table_name)})
                    app_dump.add_table(table_dump)
                if table_names:
                    result.add_app(app_dump)
            self.stdout.write(str(result))

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle.core.management.subcommands import CommandWithSubcommands
from pootle.core.schema.base import SchemaTool
from pootle.core.utils.json import jsonify

from .schema_commands import SchemaAppCommand, SchemaTableCommand


class Command(CommandWithSubcommands):
    help = "Pootle schema state command."
    requires_system_checks = False

    subcommands = {
        "app": SchemaAppCommand,
        "table": SchemaTableCommand,
    }

    def add_arguments(self, parser):

        check_or_dump_or_tables = parser.add_mutually_exclusive_group()
        check_or_dump_or_tables.add_argument(
            '--check',
            action='store_true',
            default=False,
            dest='check',
            help='Print schema state.',
        )
        check_or_dump_or_tables.add_argument(
            '--dump',
            action='store_true',
            default=False,
            dest='dump',
            help='Print schema settings.',
        )
        check_or_dump_or_tables.add_argument(
            '--tables',
            action='store_true',
            default=False,
            dest='tables',
            help='Print all table names.',
        )
        super(Command, self).add_arguments(parser)

    def handle(self, **options):
        schema_tool = SchemaTool()
        if options['tables']:
            self.stdout.write(jsonify(schema_tool.get_tables()))

        if options['check']:
            self.stdout.write('%s' % schema_tool.state)

        if options['dump']:
            self.stdout.write(
                jsonify(schema_tool.schema_dumper.get_defaults())
            )

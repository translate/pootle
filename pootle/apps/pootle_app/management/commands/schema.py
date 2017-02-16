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
from pootle.core.utils.json import jsonify


class Command(BaseCommand):
    help = "Print Pootle's current schema state."
    requires_system_checks = False

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
        schema_tool = SchemaTool()
        if options['tables']:
            self.stdout.write(jsonify(schema_tool.get_tables()))
        else:
            self.stdout.write(
                jsonify(schema_tool.get_defaults())
            )

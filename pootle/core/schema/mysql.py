# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import connection


def fetchall_asdicts(cursor, fields):
    """Return all rows from a cursor as a dict filtered by fields."""

    columns = [col[0] for col in cursor.description]
    return [
        dict(filter(lambda x: x[0].lower() in fields, zip(columns, row)))
        for row in cursor.fetchall()
    ]


class MySQLSchemaDumper(object):
    def get_defaults(self):
        sql = ("SELECT default_character_set_name, default_collation_name "
               "FROM information_schema.SCHEMATA WHERE schema_name = '%s'")
        with connection.cursor() as cursor:
            cursor.execute(sql % cursor.db.settings_dict['NAME'])
            character_set, collation = cursor.fetchone()

        return dict(character_set=character_set, collation=collation)

    def get_table_fields(self, table_name):
        fields = ('field', 'type', 'collation', 'key', 'extra')
        with connection.cursor() as cursor:
            cursor.execute("SHOW FULL COLUMNS FROM %s" % table_name)
            result = fetchall_asdicts(cursor, fields)

        return result

    def get_table_indices(self, table_name):
        fields = ('non_unique', 'key_name', 'column_name')
        with connection.cursor() as cursor:
            cursor.execute("SHOW INDEX FROM %s" % table_name)
            result = fetchall_asdicts(cursor, fields)

        return result

    def get_table_constraints(self, table_name):
        fields = ('table_name', 'column_name', 'constraint_name',
                  'referenced_table_name', 'referenced_column_name')

        sql = (
            "SELECT %s from INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
            "WHERE TABLE_NAME = '%s' AND CONSTRAINT_SCHEMA = '%s'" % (
                ', '.join(fields),
                table_name,
                connection.settings_dict['NAME'])
        )

        with connection.cursor() as cursor:
            cursor.execute(sql)
            result = fetchall_asdicts(cursor, fields)

        return result

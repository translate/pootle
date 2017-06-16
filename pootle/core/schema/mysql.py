# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.db import connection


def type_cast(value):
    if isinstance(value, long):
        return int(value)
    return value


def fetchall_asdicts(cursor, fields, sort_by_field):
    """Return all rows from a cursor as a dict filtered by fields."""

    columns = [u"%s" % col[0].lower() for col in cursor.description]
    return sorted(
        [{k: type_cast(v) for k, v in zip(columns, row) if k in fields}
         for row in cursor.fetchall()],
        key=lambda x: x.get(sort_by_field))


def list2dict(items, key_field):
    result = {}
    for d in items:
        key = d[key_field]
        if key not in result:
            del d[key_field]
            result[key] = d
        elif 'column_names' in result[key]:
            result[key]['column_names'].append(d['column_name'])
        else:
            result[key]['column_names'] = [result[key]['column_name'],
                                           d['column_name']]
            del result[key]['column_name']

    return result


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
            result = list2dict(
                fetchall_asdicts(cursor, fields, 'field'),
                'field')

        return result

    def get_table_indices(self, table_name):
        fields = ('non_unique', 'key_name', 'column_name')
        with connection.cursor() as cursor:
            cursor.execute("SHOW INDEX FROM %s" % table_name)
            result = list2dict(
                fetchall_asdicts(cursor, fields, 'column_name'),
                'key_name')

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
            result = list2dict(
                fetchall_asdicts(cursor, fields, 'column_name'),
                'constraint_name')

        return result

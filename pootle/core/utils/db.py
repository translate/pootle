# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager

from django.db import connection


@contextmanager
def useable_connection():
    connection.close_if_unusable_or_obsolete()
    yield
    connection.close_if_unusable_or_obsolete()


def set_mysql_collation_for_column(apps, cursor, model, column, collation, schema):
    """Set the collation for a mysql column if it is not set already
    """

    # Check its mysql - should probs check its not too old.
    if not hasattr(cursor.db, "mysql_version"):
        return

    # Get the db_name
    db_name = cursor.db.get_connection_params()['db']

    # Get table_name
    table_name = apps.get_model(model)._meta.db_table

    # Get the current collation
    cursor.execute(
        "SELECT COLLATION_NAME"
        " FROM `information_schema`.`columns`"
        " WHERE TABLE_SCHEMA = '%s'"
        "  AND TABLE_NAME = '%s'"
        "  AND COLUMN_NAME = '%s';"
        % (db_name, table_name, column))
    current_collation = cursor.fetchone()[0]

    if current_collation != collation:
        # set collation
        cursor.execute(
            "ALTER TABLE `%s`.`%s`"
            " MODIFY `%s`"
            "  %s"
            "  CHARACTER SET utf8"
            "  COLLATE %s"
            "  NOT NULL;"
            % (db_name, table_name,
               column, schema, collation))

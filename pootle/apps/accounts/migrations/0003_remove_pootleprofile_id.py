# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def fix_accounts_alt_src_langs(apps, schema_editor):
    """Remove pootleprofile_id column from accounts_user_alt_src_langs

    After migration from 2.5.x the pootleprofile_id column is left on
    the m2m table accounts_user_alt_src_langs causing uniqueness issues
    (#3856). This migration removes the problem column on mysql.
    """

    cursor = schema_editor.connection.cursor()

    # Check its mysql - should probs check its not too old.
    if not hasattr(cursor.db, "mysql_version"):
        return

    # Get the db_name and table_name.
    db_name = cursor.db.get_connection_params()['db']
    table_name = (apps.get_model("accounts.User")
                  ._meta.local_many_to_many[0].m2m_db_table())

    # Check the problem column exists.
    cursor.execute("SELECT COLUMN_NAME"
                   " FROM INFORMATION_SCHEMA.COLUMNS"
                   " WHERE TABLE_SCHEMA = '%s'"
                   "   AND TABLE_NAME = '%s'"
                   "   AND COLUMN_NAME = 'pootleprofile_id';"
                   % (db_name, table_name))
    if not cursor.fetchone():
        return

    # Get constraints for column.
    cursor.execute("SELECT CONSTRAINT_NAME "
                   "  FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE "
                   "  WHERE TABLE_SCHEMA = '%s' "
                   "    AND TABLE_NAME = '%s' "
                   "    AND COLUMN_NAME = 'pootleprofile_id'"
                   % (db_name, table_name))
    uniq = None
    fk = None
    default = False
    for constraint in cursor.fetchall():
        if constraint[0].endswith("uniq"):
            uniq = constraint[0]
        elif constraint[0].startswith("pootleprofile_id_refs"):
            fk = constraint[0]
        elif constraint[0] == "pootleprofile_id":
            default = True

    # Removing uniq/fk has to happen in this order.
    if uniq:
        # Remove unique constraint.
        cursor.execute("ALTER TABLE %s "
                       "  DROP KEY %s"
                       % (table_name, uniq))
    if fk:
        # Remove foreign key constraint.
        cursor.execute("ALTER TABLE %s "
                       "  DROP FOREIGN KEY %s"
                       % (table_name, fk))

    if default:
        # Remove unique constraint from older migrated db.
        cursor.execute("DROP INDEX pootleprofile_id"
                       "   ON %s;" % (table_name))

    # Remove column.
    cursor.execute("ALTER TABLE %s "
                   "  DROP COLUMN pootleprofile_id"
                   % (table_name))


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0002_user_alt_src_langs'),
    ]

    operations = [
        migrations.RunPython(fix_accounts_alt_src_langs),
    ]

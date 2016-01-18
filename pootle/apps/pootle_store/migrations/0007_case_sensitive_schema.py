# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle.core.utils.db import set_mysql_collation_for_column


def make_store_paths_cs(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    set_mysql_collation_for_column(
        apps,
        cursor,
        "pootle_store.Store",
        "pootle_path",
        "utf8_bin",
        "varchar(255)")
    set_mysql_collation_for_column(
        apps,
        cursor,
        "pootle_store.Store",
        "name",
        "utf8_bin",
        "varchar(255)")


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0006_remove_auto_now_add'),
    ]

    operations = [
        migrations.RunPython(make_store_paths_cs),
    ]

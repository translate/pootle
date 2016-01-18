# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle.core.utils.db import set_mysql_collation_for_column


def make_directory_paths_cs(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    set_mysql_collation_for_column(
        apps,
        cursor,
        "pootle_app.Directory",
        "pootle_path",
        "utf8_bin",
        "varchar(255)")
    set_mysql_collation_for_column(
        apps,
        cursor,
        "pootle_app.Directory",
        "name",
        "utf8_bin",
        "varchar(255)")


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0004_set_directory_has_no_default_permissions'),
    ]

    operations = [
        migrations.RunPython(make_directory_paths_cs),
    ]

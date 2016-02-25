# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle.core.utils.db import set_mysql_collation_for_column


def make_unit_paths_cs(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    set_mysql_collation_for_column(
        apps,
        cursor,
        "pootle_store.Unit",
        "pootle_path",
        "utf8_bin",
        "varchar(255)")


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0009_denormalize_pootle_path'),
    ]

    operations = [
        migrations.RunPython(make_unit_paths_cs),
        migrations.AlterIndexTogether(
            name='unit',
            index_together=set([('pootle_path', 'index')]),
        ),
        migrations.AlterModelOptions(
            name='unit',
            options={'ordering': ['pootle_path', 'index'], 'get_latest_by': 'mtime'},
        ),
    ]

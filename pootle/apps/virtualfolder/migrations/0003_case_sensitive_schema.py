# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle.core.utils.db import set_mysql_collation_for_column


def make_vfti_paths_cs(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    set_mysql_collation_for_column(
        apps,
        cursor,
        "virtualfolder.VirtualFolderTreeItem",
        "pootle_path",
        "utf8_bin",
        "varchar(255)")


def make_virtualfolder_paths_cs(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    set_mysql_collation_for_column(
        apps,
        cursor,
        "virtualfolder.VirtualFolder",
        "name",
        "utf8_bin",
        "varchar(70)")
    set_mysql_collation_for_column(
        apps,
        cursor,
        "virtualfolder.VirtualFolder",
        "location",
        "utf8_bin",
        "varchar(255)")


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0002_set_unit_priorities'),
    ]

    operations = [
        migrations.RunPython(make_vfti_paths_cs),
        migrations.RunPython(make_virtualfolder_paths_cs),
    ]

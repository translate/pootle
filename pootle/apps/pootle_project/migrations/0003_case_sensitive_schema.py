# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle.core.utils.db import set_mysql_collation_for_column


def make_project_codes_cs(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    set_mysql_collation_for_column(
        apps,
        cursor,
        "pootle_project.Project",
        "code",
        "utf8_bin",
        "varchar(255)")


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0002_remove_dynamic_model_choices_localfiletype'),
    ]

    operations = [
        migrations.RunPython(make_project_codes_cs),
    ]

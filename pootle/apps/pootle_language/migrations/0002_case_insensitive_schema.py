# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle.core.utils.db import set_mysql_collation_for_column


def make_lang_codes_ci(apps, schema_editor):
    cursor = schema_editor.connection.cursor()
    set_mysql_collation_for_column(
        apps,
        cursor,
        "pootle_language.Language",
        "code",
        "utf8_general_ci",
        "varchar(50)")


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_language', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(make_lang_codes_ci),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_language', '0002_case_insensitive_schema'),
        ('pootle_store', '0013_make_unit_project_notnull'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='language',
            field=models.ForeignKey(related_name='units', blank=True, to='pootle_language.Language', null=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_language', '0002_case_insensitive_schema'),
        ('pootle_project', '0010_add_reserved_code_validator'),
        ('virtualfolder', '0010_remove_virtualfolder_units'),
    ]

    operations = [
        migrations.AddField(
            model_name='virtualfolder',
            name='languages',
            field=models.ManyToManyField(related_name='vfolders', to='pootle_language.Language', db_index=True),
        ),
        migrations.AddField(
            model_name='virtualfolder',
            name='projects',
            field=models.ManyToManyField(related_name='vfolders', to='pootle_project.Project', db_index=True),
        ),
    ]

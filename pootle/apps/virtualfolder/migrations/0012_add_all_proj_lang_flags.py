# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0011_add_projects_languages'),
    ]

    operations = [
        migrations.AddField(
            model_name='virtualfolder',
            name='all_languages',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='virtualfolder',
            name='all_projects',
            field=models.BooleanField(default=False),
        ),
    ]

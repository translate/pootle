# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0013_set_projects_languages'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='virtualfolder',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='virtualfolder',
            name='location',
        ),
    ]

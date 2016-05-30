# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_statistics', '0002_update_submission_ordering'),
    ]

    operations = [
        migrations.AddField(
            model_name='scorelog',
            name='translated_wordcount',
            field=models.PositiveIntegerField(null=True),
        ),
    ]

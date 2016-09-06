# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0016_blank_last_sync_revision'),
        ('virtualfolder', '0003_case_sensitive_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='priority',
            field=models.FloatField(default=1, db_index=True, validators=[django.core.validators.MinValueValidator(0)]),
        ),
    ]

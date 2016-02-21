# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0007_case_sensitive_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='pootle_path',
            field=models.CharField(default='', unique=False, max_length=255, verbose_name='Path', db_index=True),
            preserve_default=False,
        ),
    ]

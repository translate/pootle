# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0004_index_store_index_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='priority',
            field=models.FloatField(default=1, db_index=True, validators=[django.core.validators.MinValueValidator(0)]),
            preserve_default=True,
        ),
    ]

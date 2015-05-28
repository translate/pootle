# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='directory',
            name='pootle_path',
            field=models.CharField(unique=True, max_length=255, db_index=True),
            preserve_default=True,
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0005_unit_priority'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='mtime',
            field=models.DateTimeField(auto_now=True, db_index=True),
            preserve_default=True,
        ),
    ]

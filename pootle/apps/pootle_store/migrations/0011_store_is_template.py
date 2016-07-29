# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0010_set_store_filetypes'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='is_template',
            field=models.BooleanField(default=False),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0013_set_store_filetype_again'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='revision',
            field=models.IntegerField(default=0, db_index=True, blank=True),
        ),
    ]

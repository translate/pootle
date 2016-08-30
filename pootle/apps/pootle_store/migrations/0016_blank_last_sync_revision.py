# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0015_add_slashes_validator_for_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='last_sync_revision',
            field=models.IntegerField(db_index=True, null=True, blank=True),
        ),
    ]

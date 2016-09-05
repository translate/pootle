# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0019_remove_unit_priority'),
        ('virtualfolder', '0007_make_vfolder_name_unique'),
    ]

    operations = [
        migrations.AddField(
            model_name='virtualfolder',
            name='stores',
            field=models.ManyToManyField(related_name='vfolders', to='pootle_store.Store', db_index=True),
        ),
    ]

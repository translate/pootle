# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0018_move_priority_to_store'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='unit',
            name='priority',
        ),
    ]

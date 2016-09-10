# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0009_set_vfolder_stores'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='virtualfolder',
            name='units',
        ),
    ]

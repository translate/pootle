# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0003_drop_existing_directory_default_permissions'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='directory',
            options={'ordering': ['name'], 'default_permissions': ()},
        ),
    ]

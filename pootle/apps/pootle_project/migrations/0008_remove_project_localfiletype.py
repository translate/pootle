# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0007_migrate_localfiletype'),
        ('pootle_store', '0013_set_store_filetype_again')
    ]

    operations = [
        migrations.RemoveField(
            model_name='project',
            name='localfiletype',
        ),
    ]

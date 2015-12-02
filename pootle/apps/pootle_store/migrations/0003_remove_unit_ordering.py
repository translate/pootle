# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0002_make_suggestion_user_not_null'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='unit',
            options={'get_latest_by': 'mtime'},
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0002_auto_20150205_1959'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Revision',
        ),
    ]

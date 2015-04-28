# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_statistics', '0001_initial'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='scorelog',
            unique_together=set([('submission', 'action_code')]),
        ),
    ]

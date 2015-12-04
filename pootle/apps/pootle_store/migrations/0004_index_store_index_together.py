# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0003_remove_unit_ordering'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='unit',
            index_together=set([('store', 'index')]),
        ),
    ]

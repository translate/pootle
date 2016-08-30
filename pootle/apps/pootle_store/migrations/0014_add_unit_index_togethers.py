# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0013_set_store_filetype_again'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='unit',
            index_together=set([('store', 'revision'), ('store', 'index'), ('store', 'mtime')]),
        ),
    ]

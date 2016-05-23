# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0004_correct_checkerstyle_options_order'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='treestyle',
            field=models.CharField(default=b'auto', max_length=20, verbose_name='Project Tree Style', choices=[(b'auto', 'Automatic detection of gnu/non-gnu file layouts (slower)'), (b'gnu', 'GNU style: files named by language code'), (b'nongnu', 'Non-GNU: Each language in its own directory'), (b'none', 'Allow pootle_fs to manage filesystems')]),
        ),
    ]

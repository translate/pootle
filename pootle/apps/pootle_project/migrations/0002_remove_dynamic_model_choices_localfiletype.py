# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='localfiletype',
            field=models.CharField(default='po', max_length=50, verbose_name='File Type'),
            preserve_default=True,
        ),
    ]

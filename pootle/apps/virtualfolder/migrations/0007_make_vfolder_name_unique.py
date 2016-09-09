# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0006_cleanup_vfolder_names'),
    ]

    operations = [
        migrations.AlterField(
            model_name='virtualfolder',
            name='name',
            field=models.CharField(unique=True, max_length=70, verbose_name='Name'),
        ),
    ]

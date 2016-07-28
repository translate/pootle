# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import sortedm2m.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_format', '0001_initial'),
        ('pootle_project', '0005_add_none_treestyle'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='filetypes',
            field=sortedm2m.fields.SortedManyToManyField(help_text=None, to='pootle_format.Format'),
        ),
    ]

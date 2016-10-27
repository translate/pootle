# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_format', '0002_default_formats'),
        ('pootle_store', '0008_flush_django_cache'),
    ]

    operations = [
        migrations.AddField(
            model_name='store',
            name='filetype',
            field=models.ForeignKey(related_name='stores', blank=True, to='pootle_format.Format', null=True, on_delete=models.CASCADE),
        ),
    ]

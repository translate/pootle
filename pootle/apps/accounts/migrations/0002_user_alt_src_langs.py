# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('pootle_language', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='alt_src_langs',
            field=models.ManyToManyField(to='pootle_language.Language', db_index=True, verbose_name='Alternative Source Languages', blank=True),
            preserve_default=True,
        ),
    ]

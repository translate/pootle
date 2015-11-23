# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('staticpages', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='legalpage',
            name='url',
            field=models.URLField(help_text='If set, this page will redirect to this URL', verbose_name='Redirect to URL', blank=True),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='staticpage',
            name='url',
            field=models.URLField(help_text='If set, this page will redirect to this URL', verbose_name='Redirect to URL', blank=True),
            preserve_default=True,
        ),
    ]

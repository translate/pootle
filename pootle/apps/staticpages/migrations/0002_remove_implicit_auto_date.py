# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone


class Migration(migrations.Migration):

    dependencies = [
        ('staticpages', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='agreement',
            name='agreed_on',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='legalpage',
            name='modified_on',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
        migrations.AlterField(
            model_name='staticpage',
            name='modified_on',
            field=models.DateTimeField(default=django.utils.timezone.now, editable=False),
            preserve_default=True,
        ),
    ]

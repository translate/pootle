# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0003_case_sensitive_schema'),
    ]

    operations = [
        migrations.AddField(
            model_name='virtualfolder',
            name='title',
            field=models.CharField(max_length=255, null=True, verbose_name='Title', blank=True),
        ),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0003_drop_virtualfolder_ordering'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='virtualfolder',
            name='is_browsable',
        ),
        migrations.AddField(
            model_name='virtualfolder',
            name='is_public',
            field=models.BooleanField(default=True, help_text='Whether this virtual folder is public or not.', verbose_name='Is public?'),
            preserve_default=True,
        ),
    ]

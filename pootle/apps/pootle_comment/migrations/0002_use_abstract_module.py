# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_comment', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='comment',
            name='user',
            field=models.ForeignKey(related_name='comment_comments', on_delete=django.db.models.deletion.SET_NULL, verbose_name='user', blank=True, to=settings.AUTH_USER_MODEL, null=True),
        ),
    ]

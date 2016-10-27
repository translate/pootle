# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='suggestion',
            name='user',
            field=models.ForeignKey(related_name='suggestions', to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE),
            preserve_default=True,
        ),
    ]

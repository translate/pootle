# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('evernote_auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='evernoteaccount',
            name='user',
            field=models.OneToOneField(related_name='evernote_account', to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]

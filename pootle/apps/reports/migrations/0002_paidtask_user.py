# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    # Django uses this attribute to recognize squashed migrations, but we are
    # abusing it to tell Django that this migration replaces a migration
    # already run and recorded with a different app name.
    replaces = [(b'evernote_reports', '0002_paidtask_user')]

    dependencies = [
        ('reports', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='paidtask',
            name='user',
            field=models.ForeignKey(to=settings.AUTH_USER_MODEL),
            preserve_default=True,
        ),
    ]

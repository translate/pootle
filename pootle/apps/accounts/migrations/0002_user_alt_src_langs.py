# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db.utils import OperationalError


class AddFieldIfNotExists(migrations.AddField):

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        try:
            super(AddFieldIfNotExists, self).database_forwards(
                app_label, schema_editor, from_state, to_state)
        except OperationalError:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),
        ('pootle_language', '0001_initial'),
    ]

    operations = [
        AddFieldIfNotExists(
            model_name='user',
            name='alt_src_langs',
            field=models.ManyToManyField(to='pootle_language.Language', db_index=True, verbose_name='Alternative Source Languages', blank=True),
            preserve_default=True,
        ),
    ]

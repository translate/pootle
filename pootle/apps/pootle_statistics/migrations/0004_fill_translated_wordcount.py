# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def set_translated_wordcount(apps, schema_editor):
    # this migration created some issues and has been removed
    pass

class Migration(migrations.Migration):

    dependencies = [
        ('pootle_statistics', '0003_scorelog_translated_wordcount'),
        ('pootle_store', '0008_flush_django_cache'),
    ]

    operations = [
        migrations.RunPython(set_translated_wordcount),
    ]

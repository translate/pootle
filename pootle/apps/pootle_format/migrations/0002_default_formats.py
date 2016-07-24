# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle.core.delegate import formats


def add_default_formats(apps, schema_editor):
    formats.get().initialize()


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_format', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(add_default_formats),
    ]

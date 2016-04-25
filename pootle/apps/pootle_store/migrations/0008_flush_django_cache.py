# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.management import call_command
from django.db import migrations


def flush_django_cache(apps, schema_editor):
    call_command('flush_cache', '--django-cache')


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0007_case_sensitive_schema'),
    ]

    operations = [
        migrations.RunPython(flush_django_cache),
    ]

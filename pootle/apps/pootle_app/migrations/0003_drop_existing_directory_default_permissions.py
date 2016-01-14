# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def drop_existing_directory_default_permissions(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")

    Permission.objects.filter(
        codename__in=['add_directory', 'change_directory', 'delete_directory']
    ).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0002_mark_empty_dirs_as_obsolete'),
    ]

    operations = [
        migrations.RunPython(drop_existing_directory_default_permissions),
    ]

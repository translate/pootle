# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def add_create_project_permission(apps, schema_editor):
    ContentType = apps.get_model('contenttypes.ContentType')
    Permission = apps.get_model("auth", "Permission")

    try:
        content_type = ContentType.objects.get(app_label="pootle_app",
                                               model="directory")
    except ContentType.DoesNotExist:
        # New installations get the permission created by `initdb`, once the
        # content types have been set up.
        return

    Permission.objects.get_or_create(
        content_type=content_type,
        codename="create_project",
        defaults=dict(name="Can create projects"))


def remove_create_project_permission(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")

    Permission.objects.filter(
        content_type__app_label="pootle_app",
        content_type__model="directory",
        codename="create_project").delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0019_remove_extra_indeces'),
    ]

    operations = [
        migrations.RunPython(add_create_project_permission,
                             remove_create_project_permission),
    ]

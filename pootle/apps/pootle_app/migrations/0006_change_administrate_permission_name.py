# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def change_administrate_permission_name(apps, schema_editor):
    Permission = apps.get_model("auth", "Permission")

    Permission.objects.filter(
        codename='administrate'
    ).update(
        name='Can perform administrative tasks'
    )


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0005_case_sensitive_schema'),
    ]

    operations = [
        migrations.RunPython(change_administrate_permission_name),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def set_all_fullnames(apps, schema_editor):
    Project = apps.get_model("pootle_project", "Project")
    for project in Project.objects.filter(fullname=""):
        project.fullname = project.code
        project.save()


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0008_remove_project_localfiletype'),
    ]

    operations = [
        migrations.RunPython(set_all_fullnames),
    ]

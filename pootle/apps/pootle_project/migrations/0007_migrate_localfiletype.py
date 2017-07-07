# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle.core.delegate import formats


def migrate_localfiletype(apps, schema_editor):
    format_registry = formats.get()

    projects = apps.get_model("pootle_project.Project").objects.all()
    filetypes = apps.get_model("pootle_format.Format").objects.all()

    for project in projects:
        if project.localfiletype in format_registry:
            filetype = filetypes.get(
                pk=format_registry[project.localfiletype]['pk'])
            if filetype not in project.filetypes.all():
                project.filetypes.add(filetype)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_format', '0002_default_formats'),
        ('pootle_project', '0006_project_filetypes'),
    ]

    operations = [
        migrations.RunPython(migrate_localfiletype),
    ]

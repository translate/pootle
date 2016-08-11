# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import migrations, models

from pootle.core.delegate import formats


logger = logging.getLogger(__name__)


def migrate_store_filetypes(apps, schema_editor):
    format_registry = formats.get()

    projects = apps.get_model("pootle_project.Project").objects.all()
    stores = apps.get_model("pootle_store.Store").objects.all()
    filetypes = apps.get_model("pootle_format.Format").objects.all()

    for project in projects:
        for filetype in project.filetypes.all():
            stores = (
                stores.filter(translation_project__project=project)
                      .filter(filetype__isnull=True)
                      .filter(name__endswith=".%s" % filetype.extension))
            stores.update(filetype=filetype)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0003_realpath_can_be_none'),
        ('pootle_project', '0007_migrate_localfiletype'),
        ('pootle_store', '0009_store_filetype'),
    ]

    operations = [
        migrations.RunPython(migrate_store_filetypes),
    ]

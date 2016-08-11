# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import migrations, models


logger = logging.getLogger(__name__)


def migrate_store_filetypes(apps, schema_editor):
    projects = apps.get_model("pootle_project.Project").objects.all()

    for project in projects:
        for filetype in project.filetypes.all():
            (apps.get_model("pootle_store.Store").objects.all()
                 .filter(translation_project__project=project)
                 .filter(name__endswith=".%s" % filetype.extension.name)
                 .update(filetype=filetype))
            if filetype.extension != filetype.template_extension:
                (apps.get_model("pootle_store.Store").objects.all()
                     .filter(translation_project__project=project)
                     .filter(name__endswith=".%s" % filetype.template_extension.name)
                     .update(filetype=filetype))


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0012_set_is_template'),
    ]

    operations = [
        migrations.RunPython(migrate_store_filetypes),
    ]

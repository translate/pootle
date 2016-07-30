# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import migrations, models

from pootle.core.delegate import formats
from pootle_format.exceptions import UnrecognizedFiletype
from pootle_format.utils import ProjectFiletypes


logger = logging.getLogger(__name__)


def migrate_store_is_template(apps, schema_editor):
    format_registry = formats.get()

    tps = apps.get_model("pootle_translationproject.TranslationProject").objects.all()

    for tp in tps:
        try:
            project = tp.project
        except apps.get_model("pootle_project.Project").DoesNotExist:
            logger.warn("TP with missing project '%s', not updating" % tp.pootle_path)
            continue
        if tp.language == tp.project.source_language or tp.language.code == "templates":
            tp.stores.update(is_template=True)
        else:
            tp.stores.update(is_template=False)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0011_store_is_template'),
    ]

    operations = [
        migrations.RunPython(migrate_store_is_template),
    ]

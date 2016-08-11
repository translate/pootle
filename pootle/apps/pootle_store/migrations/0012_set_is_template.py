# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import migrations, models


logger = logging.getLogger(__name__)


def migrate_store_is_template(apps, schema_editor):
    tps = apps.get_model("pootle_translationproject.TranslationProject").objects.all()

    for tp in tps:
        try:
            __ = tp.project
        except apps.get_model("pootle_project.Project").DoesNotExist:
            logger.warn("TP with missing project '%s', not updating", tp.pootle_path)
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

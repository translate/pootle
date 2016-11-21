# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import migrations, models

from pootle_data.store_data import StoreDataTool
from pootle_data.tp_data import TPDataTool


logger = logging.getLogger(__name__)


def update_tp_and_store_stats(apps, schema_editor):
    Store = apps.get_model("pootle_store.Store")
    TranslationProject = apps.get_model(
        "pootle_translationproject.TranslationProject")
    for store in Store.objects.iterator():
        logger.info("Set stats for Store: %s" % store.pootle_path)
        StoreDataTool(store).update()
    for tp in TranslationProject.objects.iterator():
        logger.info("Set stats for TP: %s" % tp.pootle_path)
        TPDataTool(tp).update()


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_data', '0006_add_cascade_deletes'),
    ]

    operations = [
        migrations.RunPython(update_tp_and_store_stats),
    ]

# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.db.utils import OperationalError

from pootle_store.constants import OBSOLETE


def make_tp_directories_obsolete(apps, schema_editor):
    TranslationProject = apps.get_model("pootle_translationproject",
                                        "TranslationProject")
    Directory = apps.get_model("pootle_app", "Directory")
    Store = apps.get_model("pootle_store", "Store")

    try:
        tps = list(TranslationProject.objects.filter(disabled=True))
    except OperationalError:
        return

    for tp in tps:
        dir = tp.directory
        directories = Directory.objects \
                               .filter(pootle_path__startswith=dir.pootle_path)
        directories.update(obsolete=True)
        stores = Store.objects.filter(pootle_path__startswith=dir.pootle_path)
        for store in stores:
            store.obsolete = True
            store.save()
            store.unit_set.update(state=OBSOLETE)


def set_tp_disabled(apps, schema_editor):
    TranslationProject = apps.get_model("pootle_translationproject",
                                        "TranslationProject")
    for tp in TranslationProject.objects.filter(directory__obsolete=True):
        tp.disabled = True
        tp.directory.obsolete = False
        tp.directory.save()
        # subdirs, stores and units will be resurrected after
        # `update_stores` is executed


class RemoveFieldIfExists(migrations.RemoveField):

    def database_forwards(self, app_label, schema_editor, from_state, to_state):
        try:
            super(RemoveFieldIfExists, self).database_forwards(
                app_label, schema_editor, from_state, to_state)
        except OperationalError:
            pass



class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0001_initial'),
        ('pootle_store', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(make_tp_directories_obsolete, set_tp_disabled),
        RemoveFieldIfExists(
            model_name='translationproject',
            name='disabled',
        ),
    ]

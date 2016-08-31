# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle_store.revision import StoreRevision


def set_store_revisions(apps, schema_editor):
    Store = apps.get_model("pootle_store.Store")
    for store in Store.objects.all():
        StoreRevision(store).update()


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0014_store_revision'),
    ]

    operations = [
        migrations.RunPython(set_store_revisions),
    ]

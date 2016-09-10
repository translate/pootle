# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def set_vfolder_stores(app, schema):
    VirtualFolder = app.get_model("virtualfolder.VirtualFolder")
    Store = app.get_model("pootle_store.Store")
    for vf in VirtualFolder.objects.all():
        store_pks = vf.units.values_list("store", flat=True).distinct()
        stores = Store.objects.filter(pk__in=store_pks)
        vf.stores.add(*stores)


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0008_virtualfolder_stores'),
    ]

    operations = [
        migrations.RunPython(set_vfolder_stores)
    ]

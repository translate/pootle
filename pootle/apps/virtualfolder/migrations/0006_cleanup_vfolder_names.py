# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from collections import Counter

from django.db import migrations, models


def rename_vf(vfolder):
    parts = vfolder.location.split("/")
    suffix = "-".join(
        [x for x
         in parts
         if x and x not in ["{LANG}", "{PROJ}"]])
    new_name = "-".join([vfolder.name, suffix])

    for vfti in vfolder.vf_treeitems.all():
        vfti_parts = vfti.pootle_path.split("/")
        vfti_parts[vfolder.location.strip("/").count("/") + 2] = new_name
        vfti.pootle_path = "/".join(vfti_parts)
        vfti.save()

    vfolder.name = new_name
    vfolder.save()


def cleanup_vfolder_names(app, schema):
    VirtualFolder = app.get_model("virtualfolder.VirtualFolder")
    names = Counter(VirtualFolder.objects.values_list("name", flat=True))
    for name, count in names.items():
        if count < 2:
            continue
        for vf in VirtualFolder.objects.filter(name=name):
            rename_vf(vf)


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0005_set_vfolder_titles'),
    ]

    operations = [
        migrations.RunPython(cleanup_vfolder_names)
    ]

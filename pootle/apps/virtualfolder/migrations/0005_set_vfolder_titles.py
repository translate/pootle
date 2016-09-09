# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def set_vfolder_titles(app, schema):
    VirtualFolder = app.get_model("virtualfolder.VirtualFolder")
    for vf in VirtualFolder.objects.all():
        vf.title = vf.name
        vf.save()

class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0004_virtualfolder_title'),
    ]

    operations = [
        migrations.RunPython(set_vfolder_titles)
    ]

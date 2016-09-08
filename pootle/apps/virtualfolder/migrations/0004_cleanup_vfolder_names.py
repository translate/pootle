# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def rename(vfolder):
    i = 0
    old_name = vfolder.name
    while True:
        if i:
            new_name = "%s-%s" % (old_name, i)
        try:
            vfolder.name = new_name
            vfolder.save()
        except ValidationError:
            i += 1
            if i > 1000:
                raise Exception(
                    "Failed to rename vfolder '%s' - please rename before "
                    "continuing."
                    % old_name)


def cleanup_vfolder_names(app, schema):
    VirtualFolderTreeItem = app.get_model("virtualfolder.VirtualFolderTreeItem")
    Directory = app.get_model("pootle_app.Directory")
    for vfti in VirtualFolderTreeItem.objects.all():
        if Directory.objects.filter(pootle_path=self.pootle_path).exists():
            old_name = vfolder.name
            rename(vfolder)
            log.warn(
                "Renamed vfolder '%' -> '%s' due to clashing directory"
                % (old_name, vfolder.name))


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0003_case_sensitive_schema'),
    ]

    operations = [
        migrations.RunPython(cleanup_vfolder_names)
    ]

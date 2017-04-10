# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def drop_vfti_ctype(apps, schema_editor):
    ContentType = apps.get_model('contenttypes.ContentType')
    ContentType.objects.filter(app_label='virtualfolder',
                               model='virtualfoldertreeitem').delete()


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0017_rm_vfdata'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='virtualfoldertreeitem',
            unique_together=set([]),
        ),
        migrations.RemoveField(
            model_name='virtualfoldertreeitem',
            name='directory',
        ),
        migrations.RemoveField(
            model_name='virtualfoldertreeitem',
            name='parent',
        ),
        migrations.RemoveField(
            model_name='virtualfoldertreeitem',
            name='stores',
        ),
        migrations.RemoveField(
            model_name='virtualfoldertreeitem',
            name='vfolder',
        ),
        migrations.DeleteModel(
            name='VirtualFolderTreeItem',
        ),
        migrations.RunPython(drop_vfti_ctype),
    ]

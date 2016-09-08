# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0005_add_stores_projs_langs_vfdata'),
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
        migrations.AlterUniqueTogether(
            name='virtualfolder',
            unique_together=set([]),
        ),
        migrations.DeleteModel(
            name='VirtualFolderTreeItem',
        ),
        migrations.RemoveField(
            model_name='virtualfolder',
            name='location',
        ),
        migrations.RemoveField(
            model_name='virtualfolder',
            name='units',
        ),
    ]

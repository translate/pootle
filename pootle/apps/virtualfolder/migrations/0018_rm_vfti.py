# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


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
    ]

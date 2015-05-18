# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pootle.core.mixins.treeitem


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0001_initial'),
        ('pootle_app', '0001_initial'),
        ('virtualfolder', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VirtualFolderTreeItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pootle_path', models.CharField(unique=True, max_length=255, editable=False, db_index=True)),
                ('directory', models.ForeignKey(related_name='vf_treeitems', to='pootle_app.Directory')),
                ('parent', models.ForeignKey(related_name='child_vf_treeitems', to='virtualfolder.VirtualFolderTreeItem', null=True)),
                ('stores', models.ManyToManyField(related_name='parent_vf_treeitems', to='pootle_store.Store', db_index=True)),
                ('vfolder', models.ForeignKey(related_name='vf_treeitems', to='virtualfolder.VirtualFolder')),
            ],
            options={
            },
            bases=(models.Model, pootle.core.mixins.treeitem.CachedTreeItem),
        ),
        migrations.AlterUniqueTogether(
            name='virtualfoldertreeitem',
            unique_together=set([('directory', 'vfolder')]),
        ),
    ]

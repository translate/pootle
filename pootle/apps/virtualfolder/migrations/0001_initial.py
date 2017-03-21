# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pootle.core.mixins.treeitem
import pootle.core.markup.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0001_initial'),
        ('pootle_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='VirtualFolder',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=70, verbose_name='Name')),
                ('location', models.CharField(help_text='Root path where this virtual folder is applied.', max_length=255, verbose_name='Location')),
                ('filter_rules', models.TextField(help_text='Filtering rules that tell which stores this virtual folder comprises.', verbose_name='Filter')),
                ('priority', models.FloatField(default=1, help_text='Number specifying importance. Greater priority means it is more important.', verbose_name='Priority')),
                ('is_public', models.BooleanField(default=True, help_text='Whether this virtual folder is public or not.', verbose_name='Is public?')),
                ('description', pootle.core.markup.fields.MarkupField(verbose_name='Description', blank=True)),
                ('units', models.ManyToManyField(related_name='vfolders', to='pootle_store.Unit', db_index=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='virtualfolder',
            unique_together=set([('name', 'location')]),
        ),
        migrations.CreateModel(
            name='VirtualFolderTreeItem',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pootle_path', models.CharField(unique=True, max_length=255, editable=False, db_index=True)),
                ('directory', models.ForeignKey(related_name='vf_treeitems', to='pootle_app.Directory', on_delete=models.CASCADE)),
                ('parent', models.ForeignKey(related_name='child_vf_treeitems', to='virtualfolder.VirtualFolderTreeItem', null=True, on_delete=models.CASCADE)),
                ('stores', models.ManyToManyField(related_name='parent_vf_treeitems', to='pootle_store.Store', db_index=True)),
                ('vfolder', models.ForeignKey(related_name='vf_treeitems', to='virtualfolder.VirtualFolder', on_delete=models.CASCADE)),
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

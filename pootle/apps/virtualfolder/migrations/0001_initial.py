# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pootle.core.markup.fields


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0001_initial'),
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
                ('is_browsable', models.BooleanField(default=True, help_text='Whether this virtual folder is active or not.', verbose_name='Is browsable?')),
                ('description', pootle.core.markup.fields.MarkupField(verbose_name='Description', blank=True)),
                ('units', models.ManyToManyField(related_name='vfolders', to='pootle_store.Unit', db_index=True)),
            ],
            options={
                'ordering': ['-priority', 'name'],
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='virtualfolder',
            unique_together=set([('name', 'location')]),
        ),
    ]

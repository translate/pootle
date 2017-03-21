# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0004_correct_checkerstyle_options_order'),
        ('pootle_store', '0008_flush_django_cache'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoreFS',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('pootle_path', models.CharField(max_length=255)),
                ('path', models.CharField(max_length=255)),
                ('last_sync_revision', models.IntegerField(null=True, blank=True)),
                ('last_sync_mtime', models.DateTimeField(null=True, blank=True)),
                ('last_sync_hash', models.CharField(max_length=64, null=True, blank=True)),
                ('staged_for_removal', models.BooleanField(default=False)),
                ('staged_for_merge', models.BooleanField(default=False)),
                ('resolve_conflict', models.IntegerField(default=0, null=True, blank=True, choices=[(0, ''), (1, 'pootle'), (2, 'fs')])),
                ('project', models.ForeignKey(related_name='store_fs', to='pootle_project.Project', on_delete=models.CASCADE)),
                ('store', models.ForeignKey(related_name='fs', on_delete=django.db.models.deletion.SET_NULL, blank=True, to='pootle_store.Store', null=True)),
            ],
            options={
                'abstract': False,
            },
        ),
    ]

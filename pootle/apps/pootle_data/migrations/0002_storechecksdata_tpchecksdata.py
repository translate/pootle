# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0003_realpath_can_be_none'),
        ('pootle_store', '0016_blank_last_sync_revision'),
        ('pootle_data', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='StoreChecksData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, db_index=True)),
                ('category', models.IntegerField(default=0, db_index=True)),
                ('count', models.IntegerField(default=0, db_index=True)),
                ('store', models.ForeignKey(related_name='check_data', to='pootle_store.Store', on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'pootle_store_check_data',
            },
        ),
        migrations.CreateModel(
            name='TPChecksData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, db_index=True)),
                ('category', models.IntegerField(default=0, db_index=True)),
                ('count', models.IntegerField(default=0, db_index=True)),
                ('tp', models.ForeignKey(related_name='check_data', to='pootle_translationproject.TranslationProject', on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'pootle_tp_check_data',
            },
        ),
    ]

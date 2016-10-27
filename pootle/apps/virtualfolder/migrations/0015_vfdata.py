# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_statistics', '0004_fill_translated_wordcount'),
        ('pootle_store', '0019_remove_unit_priority'),
        ('virtualfolder', '0014_remove_location'),
    ]

    operations = [
        migrations.CreateModel(
            name='VFData',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('max_unit_mtime', models.DateTimeField(db_index=True, null=True, blank=True)),
                ('max_unit_revision', models.IntegerField(default=0, null=True, db_index=True, blank=True)),
                ('critical_checks', models.IntegerField(default=0, db_index=True)),
                ('pending_suggestions', models.IntegerField(default=0, db_index=True)),
                ('total_words', models.IntegerField(default=0, db_index=True)),
                ('translated_words', models.IntegerField(default=0, db_index=True)),
                ('fuzzy_words', models.IntegerField(default=0, db_index=True)),
                ('last_created_unit', models.OneToOneField(related_name='last_created_for_vfdata', null=True, blank=True, to='pootle_store.Unit', on_delete=models.CASCADE)),
                ('last_submission', models.OneToOneField(related_name='vfdata_stats_data', null=True, blank=True, to='pootle_statistics.Submission', on_delete=models.CASCADE)),
                ('last_updated_unit', models.OneToOneField(related_name='last_updated_for_vfdata', null=True, blank=True, to='pootle_store.Unit', on_delete=models.CASCADE)),
                ('vf', models.OneToOneField(related_name='data', to='virtualfolder.VirtualFolder', on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'pootle_vf_data',
            },
        ),
    ]

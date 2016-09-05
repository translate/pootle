# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_statistics', '0004_fill_translated_wordcount'),
        ('pootle_store', '0016_blank_last_sync_revision'),
        ('pootle_language', '0002_case_insensitive_schema'),
        ('pootle_project', '0010_add_reserved_code_validator'),
        ('virtualfolder', '0003_case_sensitive_schema'),
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
                ('last_created_unit', models.OneToOneField(related_name='last_created_for_vfdata', null=True, blank=True, to='pootle_store.Unit')),
                ('last_submission', models.OneToOneField(related_name='vfdata_stats_data', null=True, blank=True, to='pootle_statistics.Submission')),
                ('last_updated_unit', models.OneToOneField(related_name='last_updated_for_vfdata', null=True, blank=True, to='pootle_store.Unit')),
            ],
            options={
                'db_table': 'pootle_vf_data',
            },
        ),
        migrations.AddField(
            model_name='virtualfolder',
            name='language',
            field=models.ForeignKey(related_name='vfolders', blank=True, to='pootle_language.Language', null=True),
        ),
        migrations.AddField(
            model_name='virtualfolder',
            name='project',
            field=models.ForeignKey(related_name='vfolders', blank=True, to='pootle_project.Project', null=True),
        ),
        migrations.AddField(
            model_name='virtualfolder',
            name='stores',
            field=models.ManyToManyField(related_name='vfolders', to='pootle_store.Store', db_index=True),
        ),
        migrations.AddField(
            model_name='vfdata',
            name='vf',
            field=models.OneToOneField(related_name='data', to='virtualfolder.VirtualFolder'),
        ),
    ]

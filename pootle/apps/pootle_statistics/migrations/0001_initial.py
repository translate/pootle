# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0001_initial'),
        ('pootle_store', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Submission',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_time', models.DateTimeField(db_index=True)),
                ('field', models.IntegerField(db_index=True, null=True, blank=True)),
                ('type', models.IntegerField(db_index=True, null=True, blank=True)),
                ('old_value', models.TextField(default='', blank=True)),
                ('new_value', models.TextField(default='', blank=True)),
                ('similarity', models.FloatField(null=True, blank=True)),
                ('mt_similarity', models.FloatField(null=True, blank=True)),
                ('quality_check', models.ForeignKey(blank=True, to='pootle_store.QualityCheck', null=True, on_delete=models.CASCADE)),
                ('store', models.ForeignKey(blank=True, to='pootle_store.Store', null=True, on_delete=models.CASCADE)),
                ('submitter', models.ForeignKey(to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('suggestion', models.ForeignKey(blank=True, to='pootle_store.Suggestion', null=True, on_delete=models.CASCADE)),
                ('translation_project', models.ForeignKey(to='pootle_translationproject.TranslationProject', on_delete=models.CASCADE)),
                ('unit', models.ForeignKey(blank=True, to='pootle_store.Unit', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['creation_time'],
                'db_table': 'pootle_app_submission',
                'get_latest_by': 'creation_time',
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='ScoreLog',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('creation_time', models.DateTimeField(db_index=True)),
                ('rate', models.FloatField(default=0)),
                ('review_rate', models.FloatField(default=0)),
                ('wordcount', models.PositiveIntegerField()),
                ('similarity', models.FloatField()),
                ('score_delta', models.FloatField()),
                ('action_code', models.IntegerField()),
                ('submission', models.ForeignKey(to='pootle_statistics.Submission', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='scorelog',
            unique_together=set([('submission', 'action_code')]),
        ),
    ]

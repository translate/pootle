# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import datetime
from django.utils.timezone import utc
import translate.storage.base
import pootle_store.fields
import pootle.core.mixins.treeitem
import pootle.core.storage
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pootle_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Store',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('file', pootle_store.fields.TranslationStoreField(storage=pootle.core.storage.PootleFileSystemStorage(), upload_to='', max_length=255, editable=False, db_index=True)),
                ('pootle_path', models.CharField(unique=True, max_length=255, verbose_name='Path', db_index=True)),
                ('name', models.CharField(max_length=128, editable=False)),
                ('file_mtime', models.DateTimeField(default=datetime.datetime(1, 1, 1, 0, 0, tzinfo=utc))),
                ('state', models.IntegerField(default=0, editable=False, db_index=True)),
                ('creation_time', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('last_sync_revision', models.IntegerField(null=True, db_index=True)),
                ('obsolete', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(related_name='child_stores', editable=False, to='pootle_app.Directory', on_delete=models.CASCADE)),
                ('translation_project', models.ForeignKey(related_name='stores', editable=False, to='pootle_translationproject.TranslationProject', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['pootle_path'],
            },
            bases=(models.Model, pootle.core.mixins.treeitem.CachedTreeItem, translate.storage.base.TranslationStore),
        ),
        migrations.CreateModel(
            name='Unit',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('index', models.IntegerField(db_index=True)),
                ('unitid', models.TextField(editable=False)),
                ('unitid_hash', models.CharField(max_length=32, editable=False, db_index=True)),
                ('source_f', pootle_store.fields.MultiStringField(null=True)),
                ('source_hash', models.CharField(max_length=32, editable=False, db_index=True)),
                ('source_wordcount', models.SmallIntegerField(default=0, editable=False)),
                ('source_length', models.SmallIntegerField(default=0, editable=False, db_index=True)),
                ('target_f', pootle_store.fields.MultiStringField(null=True, blank=True)),
                ('target_wordcount', models.SmallIntegerField(default=0, editable=False)),
                ('target_length', models.SmallIntegerField(default=0, editable=False, db_index=True)),
                ('developer_comment', models.TextField(null=True, blank=True)),
                ('translator_comment', models.TextField(null=True, blank=True)),
                ('locations', models.TextField(null=True, editable=False)),
                ('context', models.TextField(null=True, editable=False)),
                ('state', models.IntegerField(default=0, db_index=True)),
                ('revision', models.IntegerField(default=0, db_index=True, blank=True)),
                ('creation_time', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('mtime', models.DateTimeField(auto_now=True, auto_now_add=True, db_index=True)),
                ('submitted_on', models.DateTimeField(null=True, db_index=True)),
                ('commented_on', models.DateTimeField(null=True, db_index=True)),
                ('reviewed_on', models.DateTimeField(null=True, db_index=True)),
                ('commented_by', models.ForeignKey(related_name='commented', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('reviewed_by', models.ForeignKey(related_name='reviewed', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('store', models.ForeignKey(to='pootle_store.Store', on_delete=models.CASCADE)),
                ('submitted_by', models.ForeignKey(related_name='submitted', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['store', 'index'],
                'get_latest_by': 'mtime',
            },
            bases=(models.Model, translate.storage.base.TranslationUnit),
        ),
        migrations.CreateModel(
            name='Suggestion',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('target_f', pootle_store.fields.MultiStringField()),
                ('target_hash', models.CharField(max_length=32, db_index=True)),
                ('translator_comment_f', models.TextField(null=True, blank=True)),
                ('state', models.CharField(default='pending', max_length=16, db_index=True, choices=[('pending', 'Pending'), ('accepted', 'Accepted'), ('rejected', 'Rejected')])),
                ('creation_time', models.DateTimeField(null=True, db_index=True)),
                ('review_time', models.DateTimeField(null=True, db_index=True)),
                ('unit', models.ForeignKey(to='pootle_store.Unit', on_delete=models.CASCADE)),
                ('reviewer', models.ForeignKey(related_name='reviews', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
                ('user', models.ForeignKey(related_name='suggestions', to=settings.AUTH_USER_MODEL, null=True, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model, translate.storage.base.TranslationUnit),
        ),
        migrations.CreateModel(
            name='QualityCheck',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=64, db_index=True)),
                ('category', models.IntegerField(default=0)),
                ('message', models.TextField()),
                ('false_positive', models.BooleanField(default=False, db_index=True)),
                ('unit', models.ForeignKey(to='pootle_store.Unit', on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='unit',
            unique_together=set([('store', 'unitid_hash')]),
        ),
        migrations.AlterUniqueTogether(
            name='store',
            unique_together=set([('parent', 'name')]),
        ),
    ]

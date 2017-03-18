# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import jsonfield.fields


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Config',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('object_pk', models.CharField(max_length=255, null=True, verbose_name='object ID', blank=True)),
                ('key', models.CharField(max_length=255, verbose_name='Configuration key', db_index=True)),
                ('value', jsonfield.fields.JSONField(default='', verbose_name='Configuration value', blank=True)),
                ('content_type', models.ForeignKey(related_name='content_type_set_for_config', verbose_name='content type', blank=True, to='contenttypes.ContentType', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['pk'],
                'abstract': False,
                'db_table': 'pootle_config',
            },
        ),
        migrations.AlterIndexTogether(
            name='config',
            index_together=set([('content_type', 'object_pk')]),
        ),
    ]

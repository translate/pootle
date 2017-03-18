# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='FileExtension',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=15, verbose_name='Format filetype extension', db_index=True)),
            ],
            options={
                'abstract': False,
                'db_table': 'pootle_fileextension',
            },
        ),
        migrations.CreateModel(
            name='Format',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(unique=True, max_length=30, verbose_name='Format name', db_index=True)),
                ('title', models.CharField(max_length=255, verbose_name='Format title', db_index=True)),
                ('enabled', models.BooleanField(default=True, verbose_name='Enabled')),
                ('monolingual', models.BooleanField(default=False, verbose_name='Monolingual format')),
                ('extension', models.ForeignKey(related_name='formats', to='pootle_format.FileExtension', on_delete=models.CASCADE)),
                ('template_extension', models.ForeignKey(related_name='template_formats', to='pootle_format.FileExtension', on_delete=models.CASCADE)),
            ],
            options={
                'abstract': False,
                'db_table': 'pootle_format',
            },
        ),
        migrations.AlterUniqueTogether(
            name='format',
            unique_together=set([('title', 'extension')]),
        ),
    ]

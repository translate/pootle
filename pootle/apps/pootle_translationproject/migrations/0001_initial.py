# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pootle.core.mixins.treeitem


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0001_initial'),
        ('pootle_project', '0001_initial'),
        ('pootle_language', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='TranslationProject',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('real_path', models.FilePathField(editable=False)),
                ('pootle_path', models.CharField(unique=True, max_length=255, editable=False, db_index=True)),
                ('creation_time', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('disabled', models.BooleanField(default=False)),
                ('directory', models.OneToOneField(editable=False, to='pootle_app.Directory', on_delete=models.CASCADE)),
                ('language', models.ForeignKey(to='pootle_language.Language', on_delete=models.CASCADE)),
                ('project', models.ForeignKey(to='pootle_project.Project', on_delete=models.CASCADE)),
            ],
            options={
                'db_table': 'pootle_app_translationproject',
            },
            bases=(models.Model, pootle.core.mixins.treeitem.CachedTreeItem),
        ),
        migrations.AlterUniqueTogether(
            name='translationproject',
            unique_together=set([('language', 'project')]),
        ),
    ]

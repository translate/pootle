# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pootle.core.mixins.treeitem
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        ('auth', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Directory',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('name', models.CharField(max_length=255)),
                ('pootle_path', models.CharField(unique=True, max_length=255, db_index=True)),
                ('obsolete', models.BooleanField(default=False)),
                ('parent', models.ForeignKey(related_name='child_dirs', to='pootle_app.Directory', null=True, on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['name'],
            },
            bases=(models.Model, pootle.core.mixins.treeitem.CachedTreeItem),
        ),
        migrations.CreateModel(
            name='PermissionSet',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('directory', models.ForeignKey(related_name='permission_sets', to='pootle_app.Directory', on_delete=models.CASCADE)),
                ('negative_permissions', models.ManyToManyField(related_name='permission_sets_negative', to='auth.Permission', db_index=True)),
                ('positive_permissions', models.ManyToManyField(related_name='permission_sets_positive', to='auth.Permission', db_index=True)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='permissionset',
            unique_together=set([('user', 'directory')]),
        ),
    ]

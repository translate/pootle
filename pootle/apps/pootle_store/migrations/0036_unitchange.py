# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-18 15:38
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import pootle.core.user


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('pootle_store', '0035_set_created_by_again'),
    ]

    operations = [
        migrations.CreateModel(
            name='UnitChange',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('changed_with', models.IntegerField(db_index=True)),
                ('submitted_on', models.DateTimeField(db_index=True, null=True)),
                ('commented_on', models.DateTimeField(db_index=True, null=True)),
                ('reviewed_on', models.DateTimeField(db_index=True, null=True)),
                ('commented_by', models.ForeignKey(null=True, on_delete=models.SET(pootle.core.user.get_system_user), related_name='units_commented', to=settings.AUTH_USER_MODEL)),
                ('reviewed_by', models.ForeignKey(null=True, on_delete=models.SET(pootle.core.user.get_system_user), related_name='units_reviewed', to=settings.AUTH_USER_MODEL)),
                ('submitted_by', models.ForeignKey(null=True, on_delete=models.SET(pootle.core.user.get_system_user), related_name='units_submitted', to=settings.AUTH_USER_MODEL)),
                ('unit', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='change', to='pootle_store.Unit', unique=True)),
            ],
            options={
                'abstract': False,
                'db_table': 'pootle_store_unit_change',
            },
        ),
    ]

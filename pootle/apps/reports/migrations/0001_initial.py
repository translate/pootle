# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PaidTask',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('task_type', models.PositiveSmallIntegerField(default=0, db_index=True, verbose_name='Type', choices=[(0, 'Translation'), (1, 'Review'), (2, 'Hourly Work'), (3, 'Correction')])),
                ('amount', models.FloatField(default=0, verbose_name='Amount')),
                ('rate', models.FloatField(default=0)),
                ('datetime', models.DateTimeField(verbose_name='Date', db_index=True)),
                ('description', models.TextField(null=True, verbose_name='Description')),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

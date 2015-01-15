# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Notice',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('message', models.TextField(verbose_name='Message')),
                ('added', models.DateTimeField(auto_now_add=True, null=True, verbose_name='Added', db_index=True)),
                ('directory', models.ForeignKey(to='pootle_app.Directory')),
            ],
            options={
                'ordering': ['-added'],
            },
            bases=(models.Model,),
        ),
    ]

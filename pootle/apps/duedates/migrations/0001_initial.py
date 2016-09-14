# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
from django.conf import settings
import duedates.models


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DueDate',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('due_on', models.DateTimeField()),
                ('pootle_path', models.CharField(db_index=True, max_length=255, validators=[duedates.models.validate_pootle_path])),
                ('modified_on', models.DateTimeField(auto_now_add=True)),
                ('modified_by', models.ForeignKey(to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]

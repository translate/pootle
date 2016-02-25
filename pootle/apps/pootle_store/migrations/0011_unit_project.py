# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0003_case_sensitive_schema'),
        ('pootle_store', '0010_denormalize_pootle_path_values'),
    ]

    operations = [
        migrations.AddField(
            model_name='unit',
            name='project',
            field=models.ForeignKey(related_name='units', blank=True, to='pootle_project.Project', null=True),
        ),
    ]

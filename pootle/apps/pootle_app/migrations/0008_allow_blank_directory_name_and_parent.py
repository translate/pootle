# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import pootle_app.models.directory


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0007_add_directory_name_validation'),
    ]

    operations = [
        migrations.AlterField(
            model_name='directory',
            name='name',
            field=models.CharField(blank=True, max_length=255, validators=[pootle_app.models.directory.validate_no_slashes]),
        ),
        migrations.AlterField(
            model_name='directory',
            name='parent',
            field=models.ForeignKey(related_name='child_dirs', blank=True, to='pootle_app.Directory', null=True, on_delete=models.CASCADE),
        ),
    ]

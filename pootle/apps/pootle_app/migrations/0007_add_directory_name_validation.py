# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import pootle_app.models.directory


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0006_change_administrate_permission_name'),
    ]

    operations = [
        migrations.AlterField(
            model_name='directory',
            name='name',
            field=models.CharField(max_length=255, validators=[pootle_app.models.directory.validate_no_slashes]),
        ),
    ]

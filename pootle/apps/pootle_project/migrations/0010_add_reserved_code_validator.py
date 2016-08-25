# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import pootle_project.models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0009_set_code_as_fullname_when_no_fullname'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='code',
            field=models.CharField(max_length=255, validators=[pootle_project.models.validate_not_reserved], help_text='A short code for the project. This should only contain ASCII characters, numbers, and the underscore (_) character.', unique=True, verbose_name='Code', db_index=True),
        ),
    ]

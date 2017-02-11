# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import pootle_store.validators


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0014_add_unit_index_togethers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='name',
            field=models.CharField(max_length=128, editable=False, validators=[pootle_store.validators.validate_no_slashes]),
        ),
    ]

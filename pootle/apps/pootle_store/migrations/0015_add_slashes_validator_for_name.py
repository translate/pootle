# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models
import pootle_store.models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0014_add_unit_index_togethers'),
    ]

    operations = [
        migrations.AlterField(
            model_name='store',
            name='name',
            field=models.CharField(max_length=128, editable=False, validators=[pootle_store.models.validate_no_slashes]),
        ),
    ]

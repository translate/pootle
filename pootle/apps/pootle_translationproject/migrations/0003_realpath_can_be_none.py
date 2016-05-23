# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0002_remove_translationproject_disabled'),
    ]

    operations = [
        migrations.AlterField(
            model_name='translationproject',
            name='real_path',
            field=models.FilePathField(null=True, editable=False, blank=True),
        ),
    ]

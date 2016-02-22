# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0012_denormalize_project'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='project',
            field=models.ForeignKey(related_name='units', to='pootle_project.Project'),
        ),
    ]

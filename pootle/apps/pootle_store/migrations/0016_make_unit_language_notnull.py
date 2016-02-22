# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0015_denormalize_language'),
    ]

    operations = [
        migrations.AlterField(
            model_name='unit',
            name='language',
            field=models.ForeignKey(related_name='units', to='pootle_language.Language'),
        ),
    ]

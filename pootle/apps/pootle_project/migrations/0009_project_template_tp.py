# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0003_realpath_can_be_none'),
        ('pootle_project', '0008_remove_project_localfiletype'),
    ]

    operations = [
        migrations.AddField(
            model_name='project',
            name='template_tp',
            field=models.OneToOneField(related_name='template_project', null=True, blank=True, to='pootle_translationproject.TranslationProject', verbose_name='Templates transation project'),
        ),
    ]

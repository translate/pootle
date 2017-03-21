# -*- coding: utf-8 -*-

"""The order of the checkerstyle options changed when we moved management from
Translate Toolkit into Pootle.  This simple migration realigns then to what is
expected now, preventing false positive messages about still needing a
migration.
"""

from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_project', '0003_case_sensitive_schema'),
    ]

    operations = [
        migrations.AlterField(
            model_name='project',
            name='checkstyle',
            field=models.CharField(default='standard', max_length=50, verbose_name='Quality Checks', choices=[('creativecommons', 'creativecommons'), ('drupal', 'drupal'), ('gnome', 'gnome'), ('kde', 'kde'), ('libreoffice', 'libreoffice'), ('mozilla', 'mozilla'), ('openoffice', 'openoffice'), ('standard', 'standard'), ('terminology', 'terminology'), ('wx', 'wx')]),
        ),
    ]

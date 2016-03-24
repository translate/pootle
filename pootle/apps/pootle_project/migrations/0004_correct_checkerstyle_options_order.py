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
            field=models.CharField(default=b'standard', max_length=50, verbose_name='Quality Checks', choices=[(b'creativecommons', b'creativecommons'), (b'drupal', b'drupal'), (b'gnome', b'gnome'), (b'kde', b'kde'), (b'libreoffice', b'libreoffice'), (b'mozilla', b'mozilla'), (b'openoffice', b'openoffice'), (b'standard', b'standard'), (b'terminology', b'terminology'), (b'wx', b'wx')]),
        ),
    ]

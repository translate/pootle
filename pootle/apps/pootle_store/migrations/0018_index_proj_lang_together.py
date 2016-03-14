# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0017_make_unit_project_notnull'),
    ]

    operations = [
        migrations.AlterIndexTogether(
            name='unit',
            index_together=set([('pootle_path', 'index', 'state', 'project', 'language'), ('priority', 'pootle_path', 'index', 'state', 'project', 'language'), ('submitted_on', 'pootle_path', 'index', 'state', 'project', 'language'), ('mtime', 'pootle_path', 'index', 'state', 'project', 'language')]),
        ),
    ]

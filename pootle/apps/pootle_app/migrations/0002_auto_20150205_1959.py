# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def switch_revision_to_redis(apps, schema_editor):
    from pootle.core.models import Revision
    from pootle_store.models import Unit
    Revision.add(Unit.max_revision())


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0001_initial'),
        ('pootle_store', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(switch_revision_to_redis),
    ]

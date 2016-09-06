# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models


def move_priority_from_unit_to_store(apps, schema_editor):
    Unit = apps.get_model("pootle_store.Unit")
    Store = apps.get_model("pootle_store.Store")
    priorities = dict(
        Unit.objects.exclude(priority=1.0).values_list("store_id", "priority"))
    _prios = {}
    for store_id, priority in priorities.items():
        _prios[priority] = _prios.get(priority, [])
        _prios[priority].append(store_id)
    Store.objects.all().update(priority=1.0)
    for prio, stores in _prios.items():
        Store.objects.filter(id__in=stores).update(priority=prio)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0017_store_priority'),
    ]

    operations = [
        migrations.RunPython(move_priority_from_unit_to_store),
    ]

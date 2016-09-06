# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.core.exceptions import FieldError
from django.db import models, migrations


def forwards_units(apps, schema_editor):
    Unit = apps.get_model("pootle_store", "Unit")
    VirtualFolder = apps.get_model("virtualfolder", "VirtualFolder")
    db_alias = schema_editor.connection.alias

    # first set all Units to a priority of 1.0
    Unit.objects.update(priority=1.0)

    vf_values = (
        VirtualFolder.objects.using(db_alias)
                             .order_by("-priority")
                             .values_list("units__pk", "priority"))

    unit_prios = {}
    for unit, priority in vf_values.iterator():
        # As vf_values is ordered -priority we can just grab the first for
        # each unit.
        if unit_prios.get(unit, None) is None:
            unit_prios[unit] = priority

    unit_values = (
        Unit.objects.using(db_alias)
                    .values_list("id", "priority"))

    for pk, priority, in unit_values.iterator():
        new_priority = unit_prios.get(pk, 1.0)
        if new_priority != 1.0:
            if priority != new_priority:
                Unit.objects.filter(pk=pk).update(priority=new_priority)


def forwards(apps, schema_editor):
    # as we have no real way of controlling whether this will be
    # run before or after priority was moved to store, we need to
    # test the field exists
    try:
        apps.get_model("pootle_store.Unit").objects.filter(priority=1)
    except FieldError:
        pass
    else:
        return forwards_units(apps, schema_editor)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0005_unit_priority'),
        ('virtualfolder', '0001_initial'),
    ]

    operations = [migrations.RunPython(forwards)]

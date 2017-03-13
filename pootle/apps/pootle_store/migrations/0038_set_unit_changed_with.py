# -*- coding: utf-8 -*-
# Generated by Django 1.10.5 on 2017-02-17 11:53
from __future__ import unicode_literals

import logging
import time
from django.db import migrations


logger = logging.getLogger(__name__)


def set_unit_changed_with(apps, schema_editor):
    subs = apps.get_model("pootle_statistics.Submission").objects.all()
    UnitChange = apps.get_model("pootle_store.UnitChange")
    unit_changes = {}
    last_unit = 0
    sub_data = subs.order_by("unit_id", "-creation_time", "-id").values_list(
        "unit_id", "type")
    for unit_id, sub_type in sub_data.iterator():
        if unit_id != last_unit:
            unit_changes[sub_type] = unit_changes.get(sub_type, [])
            unit_changes[sub_type].append(unit_id)
        last_unit = unit_id
    for sub_type, ids in unit_changes.items():
        start = time.time()
        total = len(ids)
        step = 10000
        offset = 0
        while True:
            UnitChange.objects.bulk_create(
                UnitChange(
                    unit_id=unit_id,
                    changed_with=sub_type)
                for unit_id
                in ids[offset:offset + step])
            offset = offset + step
            logger.debug(
                "Added %s/%s of '%s' UnitChange objects in %s seconds"
                % (min(offset, total),
                   total,
                   sub_type,
                   (time.time() - start)))
            if offset >= total:
                break


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0037_unitsource_fields'),
        ('pootle_statistics', '0012_remove_create_subs'),
    ]

    operations = [
        migrations.RunPython(set_unit_changed_with),
    ]

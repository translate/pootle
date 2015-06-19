# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def rename_reports_table_if_necessary(apps, schema_editor):
    old_db_table = 'evernote_reports_paidtask'

    if old_db_table in schema_editor.connection.introspection.table_names():
        # Rename only if the old DB table is present.
        PaidTask = apps.get_model("reports", "PaidTask")
        schema_editor.alter_db_table(PaidTask, old_db_table, 'reports_paidtask')


class Migration(migrations.Migration):

    dependencies = [
        ('reports', '0002_paidtask_user'),
    ]

    operations = [
        migrations.RunPython(rename_reports_table_if_necessary),
    ]

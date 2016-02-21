from __future__ import unicode_literals

from django.db import migrations, models


def denormalize_pootle_path(apps, schema_editor):

    Store = apps.get_model("pootle_store", "Store")
    Unit = apps.get_model("pootle_store", "Unit")
    paths = Store.objects.values_list("pootle_path", flat=True)
    for pootle_path in paths.iterator():
        Unit.objects.filter(
            store__pootle_path=pootle_path).update(pootle_path=pootle_path)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0008_unit_pootle_path'),
    ]

    operations = [
        migrations.RunPython(denormalize_pootle_path),
    ]

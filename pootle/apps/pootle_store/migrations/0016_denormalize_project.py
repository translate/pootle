from __future__ import unicode_literals

from django.db import migrations, models


def denormalize_project(apps, schema_editor):
    Unit = apps.get_model("pootle_store", "Unit")
    Store = apps.get_model("pootle_store", "Store")
    stores = Store.objects.values_list(
        "pk", "translation_project__project_id")

    for store_id, project_id in stores.iterator():
        if not project_id:
            continue 
        units = Unit.objects.filter(
            store_id=store_id).exclude(project_id=project_id)
        if units.count() == 0:
            continue
        units.update(project_id=project_id)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0002_remove_translationproject_disabled'),
        ('pootle_store', '0015_unit_project')
    ]

    operations = [
        migrations.RunPython(denormalize_project),
    ]

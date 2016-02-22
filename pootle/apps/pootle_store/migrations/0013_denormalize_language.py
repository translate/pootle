from __future__ import unicode_literals

from django.db import migrations, models

def denormalize_language(apps, schema_editor):
    Unit = apps.get_model("pootle_store", "Unit")
    Store = apps.get_model("pootle_store", "Store")
    stores = Store.objects.values_list(
        "pk", "translation_project__language_id")

    for store_id, language_id in stores.iterator():
        if not language_id:
            continue 
        units = Unit.objects.filter(
            store_id=store_id).exclude(language_id=language_id)
        if units.count() == 0:
            continue
        units.update(language_id=language_id)

class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0012_unit_language')
    ]

    operations = [
        migrations.RunPython(denormalize_language),
    ]

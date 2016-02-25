from __future__ import unicode_literals

from django.db import migrations, models


def denormalize_language(apps, schema_editor):
    TranslationProject = apps.get_model(
        "pootle_translationproject", "TranslationProject")
    Unit = apps.get_model("pootle_store", "Unit")

    tps = TranslationProject.objects.values_list(
        "pk", "language_id")

    for tp_id, language_id in tps:
        units = Unit.objects.filter(
            store__translation_language_id=tp_id).exclude(language_id=language_id)
        units.update(project_id=project_id)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_store', '0014_unit_language')
    ]

    operations = [
        migrations.RunPython(denormalize_language),
    ]

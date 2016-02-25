from __future__ import unicode_literals

from django.db import migrations, models


def denormalize_project(apps, schema_editor):
    TranslationProject = apps.get_model(
        "pootle_translationproject", "TranslationProject")
    Unit = apps.get_model("pootle_store", "Unit")

    tps = TranslationProject.objects.values_list(
        "pk", "project_id")

    for tp_id, project_id in tps:
        units = Unit.objects.filter(
            store__translation_project_id=tp_id).exclude(project_id=project_id)
        units.update(project_id=project_id)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0002_remove_translationproject_disabled'),
        ('pootle_store', '0011_unit_project')
    ]

    operations = [
        migrations.RunPython(denormalize_project),
    ]

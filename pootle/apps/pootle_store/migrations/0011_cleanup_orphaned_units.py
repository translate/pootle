from __future__ import unicode_literals

from django.db import migrations, models


def cleanup_orphaned_units(apps, schema_editor):
    Unit = apps.get_model("pootle_store", "Unit")
    Project = apps.get_model("pootle_project", "Project")
    Language = apps.get_model("pootle_language", "Language")

    project_ids = Project.objects.values_list("pk", flat=True)
    language_ids = Language.objects.values_list("pk", flat=True)

    Unit.objects.exclude(store__translation_project__project_id__in=project_ids).delete()
    Unit.objects.exclude(store__translation_project__language_id__in=language_ids).delete()


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0002_remove_translationproject_disabled'),
        ('pootle_store', '0010_unit_path_schema')
    ]

    operations = [
        migrations.RunPython(cleanup_orphaned_units),
    ]




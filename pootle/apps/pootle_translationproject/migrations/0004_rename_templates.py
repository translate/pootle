# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle_translationproject.utils import TPTool


def rename_templates(apps, schema_editor):
    projects = apps.get_model("pootle_project.Project").objects.all()
    TP = apps.get_model("pootle_translationproject.TranslationProject")
    Language = apps.get_model("pootle_language.Language")
    to_update = None
    for project in projects:
        source_lang = project.source_language
        try:
            templates = project.translationproject_set.get(
                language__code="templates")
            # there is a tp called "templates"
            # - dont do anything
            continue
        except TP.DoesNotExist:
            pass
        try:
            templates = project.translationproject_set.get(
                language=source_lang)
        except TP.DoesNotExist:
            # there is nothing that looks like a templates tp
            continue
        to_update.append((project, templates))
    if not to_update:
        return
    try:
        template_lang = Language.objects.get(code="templates")
    except:
        template_lang = Language.objects.create(code="templates")

    for project, templates in to_update:
        TPTool(project).set_language(templates, template_lang)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0003_realpath_can_be_none'),
    ]

    operations = [
        migrations.RunPython(rename_templates),
    ]

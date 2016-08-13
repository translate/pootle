# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle_config.utils import ObjectConfig
from pootle_store.constants import FUZZY, TRANSLATED
from pootle_translationproject.utils import TPTool


def rename_templates(apps, schema_editor):
    projects = apps.get_model("pootle_project.Project").objects.all()
    Language = apps.get_model("pootle_language.Language")
    Directory = apps.get_model("pootle_app.Directory")
    Unit = apps.get_model("pootle_store.Unit")
    to_update = []
    for project in projects:
        templates = project.translationproject_set.filter(
            language__code="templates")
        if templates.exists():
            continue
        source_tp = project.translationproject_set.filter(
            language=project.source_language)
        if not source_tp.exists():
            continue
        to_update.append((project, source_tp[0]))
    if not to_update:
        return
    template_lang, created_ = Language.objects.get_or_create(code="templates")
    for project, source_tp in to_update:
        existing_dir = Directory.objects.filter(
            pootle_path="/templates/%s/" % project.code)
        if existing_dir.exists():
            existing_dir.delete()
        translated_units = Unit.objects.filter(
            store__translation_project=source_tp).filter(state__in=[TRANSLATED, FUZZY])
        cloned = False
        if translated_units.exists():
            cloned = True
            TPTool(project).clone(source_tp, template_lang, update_cache=False)
        else:
            TPTool(project).move(source_tp, template_lang, update_cache=False)
        if not cloned:
            config = ObjectConfig(project)
            lang_mapping = config.get("pootle.core.lang_mapping", {}) or {}
            lang_mapping[source_tp.language.code] = "templates"
            config["pootle.core.lang_mapping"] = lang_mapping


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_translationproject', '0003_realpath_can_be_none'),
    ]

    operations = [
        migrations.RunPython(rename_templates),
    ]

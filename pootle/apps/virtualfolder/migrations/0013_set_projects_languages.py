# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations, models

from pootle.core.url_helpers import split_pootle_path


def parse_vfolder_rules(vf):
    languages = set()
    projects = set()
    new_rules = set()

    full_rules = [vf.location.strip() + rule.strip()
                  for rule in vf.filter_rules.split(",")]

    for full_rule in full_rules:
        lang_code, proj_code, dir_path, filename = split_pootle_path(full_rule)
        if filename:
            new_rules.add(dir_path + filename)
        else:
            new_rules.add(dir_path + "*")
        languages.add(lang_code)
        projects.add(proj_code)

    if "{LANG}" in languages:
        languages = set()

    if "{PROJ}" in projects:
        projects = set()

    new_rules=",".join(new_rules)

    return languages, projects, new_rules


def set_projects_and_languages(app, schema):
    VirtualFolder = app.get_model("virtualfolder.VirtualFolder")
    Project = app.get_model("pootle_project.Project")
    Language = app.get_model("pootle_language.Language")
    for vf in VirtualFolder.objects.all():
        languages, projects, new_rules = parse_vfolder_rules(vf)
        if projects:
            vf.projects.add(*Project.objects.filter(code__in=projects))
        if languages:
            vf.languages.add(*Language.objects.filter(code__in=languages))
        vf.filter_rules = new_rules
        vf.all_projects = not projects
        vf.all_languages = not languages
        vf.save()


class Migration(migrations.Migration):

    dependencies = [
        ('virtualfolder', '0012_add_all_proj_lang_flags'),
    ]

    operations = [
        migrations.RunPython(set_projects_and_languages)
    ]

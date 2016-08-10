# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


def make_dir_obsolete(directory):
    """Make directory and its parents obsolete if a parent contains one empty
    directory only
    """
    p = directory.parent
    if p is not None and p.child_dirs.filter(obsolete=False).count() == 1:
        make_dir_obsolete(p)

    directory.obsolete = True
    directory.save()


def make_empty_directories_obsolete(apps, schema_editor):
    Directory = apps.get_model("pootle_app", "Directory")
    from pootle.core.url_helpers import split_pootle_path
    for d in Directory.objects.filter(child_stores__isnull=True,
                                      child_dirs__isnull=True,
                                      obsolete=False):
        lang_code, prj_code, dir_path = split_pootle_path(d.pootle_path)[:3]

        # makeobsolete translation project directories and lower
        # and do not touch language and project directories
        if lang_code and prj_code:
            make_dir_obsolete(d)


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0001_initial'),
        ('pootle_store', '0001_initial'),
    ]

    operations = [
        migrations.RunPython(make_empty_directories_obsolete),
    ]

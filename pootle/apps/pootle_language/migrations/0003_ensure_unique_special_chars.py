# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import logging

from django.db import migrations, models


logger = logging.getLogger(__name__)


def remove_duplicate_special_characters(apps, schema_editor):
    Language = apps.get_model("pootle_language", "Language")
    for language in Language.objects.exclude(specialchars__exact=u""):
        special_chars = []
        for special_char in language.specialchars:
            if special_char in special_chars:
                continue
            special_chars.append(special_char)
        if len(special_chars) < language.specialchars:
            logger.info("Removed duplicate specialchars for %s" % language.code)
        language.specialchars = u"".join(special_chars)
        language.save()


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_language', '0002_case_insensitive_schema'),
    ]

    operations = [
        migrations.RunPython(remove_duplicate_special_characters),
    ]

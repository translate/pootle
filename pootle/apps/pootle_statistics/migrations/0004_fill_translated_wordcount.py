# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import migrations


def set_translated_wordcount(apps, schema_editor):
    from pootle_statistics.models import ScoreLog, TranslationActionCodes

    scorelog_qs = ScoreLog.objects.select_related(
        'submission',
        'submission__suggestion',
        'submission__unit'
    ).filter(
        action_code__in=[
            TranslationActionCodes.NEW,
            TranslationActionCodes.EDITED,
            TranslationActionCodes.SUGG_ACCEPTED,
            TranslationActionCodes.SUGG_REVIEWED_ACCEPTED,
        ]
    )
    for scorelog in scorelog_qs.iterator():
        translated = scorelog.get_paid_wordcounts()[0]
        ScoreLog.objects.filter(id=scorelog.id).update(
            translated_wordcount=translated
        )


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_statistics', '0003_scorelog_translated_wordcount'),
        ('pootle_store', '0008_flush_django_cache'),
    ]

    operations = [
        migrations.RunPython(set_translated_wordcount),
    ]

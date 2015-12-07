# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_language', '0001_initial'),
    ]

    operations = [
        migrations.AlterField(
            model_name='language',
            name='pluralequation',
            field=models.CharField(help_text='For more information, visit <a href="http://docs.translatehouse.org/projects/localization-guide/en/latest/l10n/pluralforms.html">our page</a> on plural forms.', max_length=512, verbose_name='Plural Equation', blank=True),
            preserve_default=True,
        ),
    ]

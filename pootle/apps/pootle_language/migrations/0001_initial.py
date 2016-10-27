# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pootle.core.mixins.treeitem


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Language',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(help_text='ISO 639 language code for the language, possibly followed by an underscore (_) and an ISO 3166 country code. <a href="http://www.w3.org/International/articles/language-tags/">More information</a>', unique=True, max_length=50, verbose_name='Code', db_index=True)),
                ('fullname', models.CharField(max_length=255, verbose_name='Full Name')),
                ('specialchars', models.CharField(help_text='Enter any special characters that users might find difficult to type', max_length=255, verbose_name='Special Characters', blank=True)),
                ('nplurals', models.SmallIntegerField(default=0, help_text='For more information, visit <a href="http://docs.translatehouse.org/projects/localization-guide/en/latest/l10n/pluralforms.html">our page</a> on plural forms.', verbose_name='Number of Plurals', choices=[(0, 'Unknown'), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6)])),
                ('pluralequation', models.CharField(help_text='For more information, visit <a href="http://docs.translatehouse.org/projects/localization-guide/en/latest/l10n/pluralforms.html">our page</a> on plural forms.', max_length=255, verbose_name='Plural Equation', blank=True)),
                ('directory', models.OneToOneField(editable=False, to='pootle_app.Directory', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['code'],
                'db_table': 'pootle_app_language',
            },
            bases=(models.Model, pootle.core.mixins.treeitem.TreeItem),
        ),
    ]

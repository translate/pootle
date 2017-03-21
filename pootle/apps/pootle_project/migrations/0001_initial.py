# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pootle.core.mixins.treeitem
import pootle_project.models


class Migration(migrations.Migration):

    dependencies = [
        ('pootle_language', '0001_initial'),
        ('pootle_app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Project',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('code', models.CharField(help_text='A short code for the project. This should only contain ASCII characters, numbers, and the underscore (_) character.', unique=True, max_length=255, verbose_name='Code', db_index=True)),
                ('fullname', models.CharField(max_length=255, verbose_name='Full Name')),
                ('checkstyle', models.CharField(default='standard', max_length=50, verbose_name='Quality Checks', choices=[('standard', 'standard'), ('creativecommons', 'creativecommons'), ('drupal', 'drupal'), ('gnome', 'gnome'), ('kde', 'kde'), ('libreoffice', 'libreoffice'), ('mozilla', 'mozilla'), ('openoffice', 'openoffice'), ('terminology', 'terminology'), ('wx', 'wx')])),
                ('localfiletype', models.CharField(default='po', max_length=50, verbose_name='File Type', choices=[('po', 'Gettext PO'), ('xlf', 'XLIFF'), ('xliff', 'XLIFF'), ('ts', 'Qt ts'), ('tmx', 'TMX'), ('tbx', 'TBX'), ('catkeys', 'Haiku catkeys'), ('csv', 'Excel CSV'), ('lang', 'Mozilla .lang')])),
                ('treestyle', models.CharField(default='auto', max_length=20, verbose_name='Project Tree Style', choices=[('auto', 'Automatic detection (slower)'), ('gnu', 'GNU style: files named by language code'), ('nongnu', 'Non-GNU: Each language in its own directory')])),
                ('ignoredfiles', models.CharField(default='', max_length=255, verbose_name='Ignore Files', blank=True)),
                ('report_email', models.EmailField(help_text='An email address where issues with the source text can be reported.', max_length=254, verbose_name='Errors Report Email', blank=True)),
                ('screenshot_search_prefix', models.URLField(null=True, verbose_name='Screenshot Search Prefix', blank=True)),
                ('creation_time', models.DateTimeField(db_index=True, auto_now_add=True, null=True)),
                ('disabled', models.BooleanField(default=False, verbose_name='Disabled')),
                ('directory', models.OneToOneField(editable=False, to='pootle_app.Directory', on_delete=models.CASCADE)),
                ('source_language', models.ForeignKey(verbose_name='Source Language', to='pootle_language.Language', on_delete=models.CASCADE)),
            ],
            options={
                'ordering': ['code'],
                'db_table': 'pootle_app_project',
            },
            bases=(models.Model, pootle.core.mixins.treeitem.CachedTreeItem, pootle_project.models.ProjectURLMixin),
        ),
    ]

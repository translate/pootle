# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import pootle.core.markup.fields
import django.utils.timezone
from django.conf import settings


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='LegalPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=False, help_text='Whether this page is active or not.', verbose_name='Active')),
                ('virtual_path', models.CharField(default='', help_text='/pages/', unique=True, max_length=100, verbose_name='Virtual Path')),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('body', pootle.core.markup.fields.MarkupField(help_text='Allowed markup: HTML', verbose_name='Display Content', blank=True)),
                ('url', models.URLField(help_text='If set, any references to this page will redirect to this URL', verbose_name='Redirect to URL', blank=True)),
                ('modified_on', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='StaticPage',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('active', models.BooleanField(default=False, help_text='Whether this page is active or not.', verbose_name='Active')),
                ('virtual_path', models.CharField(default='', help_text='/pages/', unique=True, max_length=100, verbose_name='Virtual Path')),
                ('title', models.CharField(max_length=100, verbose_name='Title')),
                ('body', pootle.core.markup.fields.MarkupField(help_text='Allowed markup: HTML', verbose_name='Display Content', blank=True)),
                ('url', models.URLField(help_text='If set, any references to this page will redirect to this URL', verbose_name='Redirect to URL', blank=True)),
                ('modified_on', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
            ],
            options={
                'abstract': False,
            },
            bases=(models.Model,),
        ),
        migrations.CreateModel(
            name='Agreement',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('agreed_on', models.DateTimeField(default=django.utils.timezone.now, editable=False)),
                ('document', models.ForeignKey(to='staticpages.LegalPage', on_delete=models.CASCADE)),
                ('user', models.ForeignKey(to=settings.AUTH_USER_MODEL, on_delete=models.CASCADE)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
        migrations.AlterUniqueTogether(
            name='agreement',
            unique_together=set([('user', 'document')]),
        ),
    ]

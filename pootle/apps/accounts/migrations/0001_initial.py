# -*- coding: utf-8 -*-
from __future__ import unicode_literals

from django.db import models, migrations
import django.utils.timezone
import re
import django.core.validators


class Migration(migrations.Migration):

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.AutoField(verbose_name='ID', serialize=False, auto_created=True, primary_key=True)),
                ('password', models.CharField(max_length=128, verbose_name='password')),
                ('last_login', models.DateTimeField(default=django.utils.timezone.now, verbose_name='last login')),
                ('username', models.CharField(help_text='Required. 30 characters or fewer. Letters, numbers and @/./+/-/_ characters', unique=True, max_length=30, verbose_name='Username', validators=[django.core.validators.RegexValidator(re.compile('^[\\w.@+-]+$'), 'Enter a valid username.', 'invalid')])),
                ('email', models.EmailField(max_length=255, verbose_name='Email Address')),
                ('full_name', models.CharField(max_length=255, verbose_name='Full Name', blank=True)),
                ('is_active', models.BooleanField(default=True, help_text='Designates whether this user should be treated as active. Unselect this instead of deleting accounts.', verbose_name='Active')),
                ('is_superuser', models.BooleanField(default=False, help_text='Designates that this user has all permissions without explicitly assigning them.', verbose_name='Superuser Status')),
                ('date_joined', models.DateTimeField(default=django.utils.timezone.now, verbose_name='date joined')),
                ('unit_rows', models.SmallIntegerField(default=9, verbose_name='Number of Rows')),
                ('rate', models.FloatField(default=0, verbose_name='Rate')),
                ('review_rate', models.FloatField(default=0, verbose_name='Review Rate')),
                ('hourly_rate', models.FloatField(default=0, verbose_name='Hourly Rate')),
                ('score', models.FloatField(default=0, verbose_name='Score')),
                ('currency', models.CharField(blank=True, max_length=3, null=True, verbose_name='Currency', choices=[('USD', 'USD'), ('EUR', 'EUR'), ('CNY', 'CNY'), ('JPY', 'JPY')])),
                ('is_employee', models.BooleanField(default=False, verbose_name='Is employee?')),
                ('twitter', models.CharField(max_length=15, null=True, verbose_name='Twitter', blank=True)),
                ('website', models.URLField(null=True, verbose_name='Website', blank=True)),
                ('linkedin', models.URLField(null=True, verbose_name='LinkedIn', blank=True)),
                ('bio', models.TextField(null=True, verbose_name='Short Bio', blank=True)),
            ],
            options={
            },
            bases=(models.Model,),
        ),
    ]

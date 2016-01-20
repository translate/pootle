#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from pootle_statistics.models import ScoreLog


class Command(BaseCommand):
    help = "Refresh score"

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            dest='reset',
            default=False,
            help='Reset all scores to zero',
        )

    def handle(self, **options):

        if options['reset']:
            User = get_user_model()
            User.objects.all().update(score=0)
            ScoreLog.objects.all().delete()

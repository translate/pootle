# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "List language codes."

    def add_arguments(self, parser):
        parser.add_argument(
            '--project',
            action='append',
            dest='projects',
            help='Limit to PROJECTS',
        )
        parser.add_argument(
            "--modified-since",
            action="store",
            dest="modified_since",
            type=int,
            default=0,
            help="Only process translations newer than specified "
                 "revision",
        )

    def handle(self, **options):
        self.list_languages(**options)

    def list_languages(self, **options):
        """List all languages on the server or the given projects."""
        from pootle_translationproject.models import TranslationProject
        tps = TranslationProject.objects.distinct()
        tps = tps.exclude(
            language__code='templates').order_by('language__code')

        if options['modified_since'] > 0:
            tps = tps.filter(
                submission__unit__revision__gt=options['modified_since'])

        if options['projects']:
            tps = tps.filter(project__code__in=options['projects'])

        for lang in tps.values_list('language__code', flat=True):
            self.stdout.write(lang)

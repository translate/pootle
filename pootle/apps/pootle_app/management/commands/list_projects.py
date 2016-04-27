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

from pootle_project.models import Project


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument(
            "--modified-since",
            action="store",
            dest="revision",
            type=int,
            default=0,
            help="Only process translations newer than specified revision",
        )

    def handle(self, **options):
        self.list_projects(**options)

    def list_projects(self, **options):
        """List all projects on the server."""

        if options['revision'] > 0:
            from pootle_translationproject.models import TranslationProject
            tps = TranslationProject.objects.filter(
                submission__id__gt=options['revision']) \
                .distinct().values("project__code")

            for tp in tps:
                self.stdout.write(tp["project__code"])
        else:
            for project in Project.objects.all():
                self.stdout.write(project.code)

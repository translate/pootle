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

from pootle.core.delegate import score_updater
from pootle_translationproject.models import TranslationProject

from . import PootleCommand


class Command(PootleCommand):
    help = "Refresh score"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--reset',
            action='store_true',
            dest='reset',
            default=False,
            help='Reset all scores to zero',
        )
        parser.add_argument(
            '--user',
            action='append',
            dest='users',
            help='User to refresh',
        )

    def get_users(self, **options):
        return (
            list(get_user_model().objects.filter(
                username__in=options["users"]).values_list("pk", flat=True))
            if options["users"]
            else None)

    def handle_all_stores(self, translation_project, **options):
        users = self.get_users(**options)
        updater = score_updater.get(TranslationProject)(translation_project)
        if options["reset"]:
            updater.clear(users)
        else:
            updater.refresh_scores(users)

    def handle_all(self, **options):
        if not self.projects and not self.languages:
            users = self.get_users(**options)
            if options["reset"]:
                score_updater.get(get_user_model())(users=users).clear()
            else:
                score_updater.get(get_user_model())().refresh_scores(users)
        else:
            super(Command, self).handle_all(**options)

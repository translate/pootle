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
from django.dispatch import receiver

from pootle.core.contextmanagers import keep_data
from pootle.core.delegate import score_updater
from pootle.core.signals import update_scores
from pootle_translationproject.models import TranslationProject


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
        parser.add_argument(
            '--user',
            action='append',
            dest='users',
            help='User to refresh',
        )

    def handle(self, **options):
        users = (
            list(get_user_model().objects.filter(
                username__in=options["users"]).values_list("pk", flat=True))
            if options["users"]
            else None)
        if options["reset"]:
            score_updater.get(get_user_model())(users=users).clear()
            return

        class Update:
            users = set()

        for tp in TranslationProject.objects.all():
            update = Update()
            with keep_data(suppress=(TranslationProject, )):

                @receiver(update_scores, sender=TranslationProject)
                def handle_update_tp_scores(**kwargs):
                    update.users = update.users | kwargs.get("users", set())

                for store in tp.stores.all():
                    update_scores.send(
                        store.__class__,
                        instance=store,
                        users=users)
            if update.users:
                update_scores.send(
                    tp.__class__,
                    instance=tp,
                    users=update.users)

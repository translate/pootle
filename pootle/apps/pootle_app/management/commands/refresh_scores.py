# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.


import datetime
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand

from pootle.core.delegate import score_updater
from pootle_store.models import Store


class Command(BaseCommand):
    help = "Refresh scores"

    def handle(self, **options):
        self.stdout.write('Start running of refresh_scores command...')

        User = get_user_model()
        users = User.objects.all()
        users.update(score=0)

        start = datetime.datetime.now()

        for store in Store.objects.all().iterator():
            updater = score_updater.get(Store)(store)
            updater.update()

        end = datetime.datetime.now()
        self.stdout.write('All done in %s.' % (end - start))

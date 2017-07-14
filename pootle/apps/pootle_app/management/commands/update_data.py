# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle.core.signals import update_data
from pootle_app.management.commands import PootleCommand
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject


logger = logging.getLogger(__name__)


class Command(PootleCommand):
    help = "Update stats data"

    def add_arguments(self, parser):
        super(Command, self).add_arguments(parser)
        parser.add_argument(
            '--store',
            action='append',
            dest='stores',
            help='Store to update data')

    def handle_stores(self, stores):
        stores = Store.objects.filter(pootle_path__in=stores)
        tps = set()
        for store in stores:
            update_data.send(store.__class__, instance=store)
            logger.debug(
                "Updated data for store: %s",
                store.pootle_path)
            tps.add(store.tp)
        for tp in tps:
            update_data.send(tp.__class__, instance=tp)
            logger.debug(
                "Updated data for translation project: %s",
                tp.pootle_path)

    def handle(self, **options):
        projects = options.get("projects")
        languages = options.get("languages")
        stores = options.get("stores")
        tps = TranslationProject.objects.all()
        if stores:
            return self.handle_stores(stores)
        if projects:
            tps = tps.filter(project__code__in=projects)
        if languages:
            tps = tps.filter(language__code__in=languages)
        for tp in tps:
            for store in tp.stores.all():
                update_data.send(store.__class__, instance=store)
                logger.debug(
                    "Updated data for store: %s",
                    store.pootle_path)
            update_data.send(tp.__class__, instance=tp)
            logger.debug(
                "Updated data for translation project: %s",
                tp.pootle_path)

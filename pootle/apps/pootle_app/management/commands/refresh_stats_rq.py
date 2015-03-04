#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import os

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from pootle_store.models import Store

from . import PootleCommand


logger = logging.getLogger('stats')


class Command(PootleCommand):
    help = "Allow stats and text indices to be refreshed manually."

    cached_methods = None
    process_disabled_projects = True

    def handle_all_stores(self, translation_project, **options):
        store_filter = {
            'translation_project': translation_project,
        }

        self.process(store_filter=store_filter, **options)

    def handle_store(self, store, **options):
        store_filter = {
            'pk': store.pk,
        }

        self.process(store_filter=store_filter, **options)

    def process(self, store_filter=None, **options):
        stores = Store.objects.live()
        if store_filter:
            stores = stores.filter(**store_filter)

        for store in stores.iterator():
            logger.info('Add job to update stats for %s' % store.pootle_path)
            store.update_all_cache()

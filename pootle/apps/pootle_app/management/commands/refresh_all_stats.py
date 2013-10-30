#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

import logging
import time
import datetime

from pootle_app.management.commands import PootleCommand

from django.db.models import Count, Max, Sum
from django.utils.encoding import iri_to_uri
from django.core.cache import cache
from django.conf import settings

from pootle_statistics.models import Submission
from pootle_language.models import Language
from pootle_store.models import Store, Unit, QualityCheck, Suggestion
from pootle_store.util import OBSOLETE, UNTRANSLATED, FUZZY, TRANSLATED


class Command(PootleCommand):
    help = "Allow stats and text indices to be refreshed manually."

    def handle_noargs(self, **options):
        # adjust debug level to the verbosity option
        verbosity = int(options.get('verbosity', 1))
        debug_levels = {
            0: logging.ERROR,
            1: logging.WARNING,
            2: logging.INFO,
            3: logging.DEBUG
        }
        debug_level = debug_levels.get(verbosity, logging.DEBUG)
        logging.getLogger().setLevel(debug_level)

        # reduce size of parse pool early on
        self.name = self.__class__.__module__.split('.')[-1]

        # info start
        start = datetime.datetime.now()
        logging.info('Start running of %s', self.name)
        timeout = settings.OBJECT_CACHE_TIMEOUT

        self._set_empty_values(timeout)
        self._set_last_action_stats(timeout)
        self._set_wordcount_stats(timeout)
        self._set_qualitycheck_stats(timeout)
        self._set_suggestion_stats(timeout)

        logging.info('Refreshing directories stats...')

        lang_query = Language.objects.all()
        for lang in lang_query:
            lang.get_stats()
            lang.get_checks()

        # info finish
        end = datetime.datetime.now()
        logging.info('All done for %s in %s', self.name, end - start)

    def _set_qualitycheck_stats_cache(self, stats, key, timeout):
        if key:
            logging.info('Set get_checks for %s' % key)
            cache.set(key + ':get_checks', stats, timeout)

    def _set_qualitycheck_stats(self, timeout):
        queryset = QualityCheck.objects.filter(unit__state__gt=UNTRANSLATED,
                                               false_positive=False) \
                                       .values('unit__store', 'name') \
                                       .annotate(count=Count('name')) \
                                       .order_by('unit__store')

        saved = None
        key = None
        stats = {}

        for item in queryset:
            if item['unit__store'] != saved:
                key = Store.objects.get(id=item['unit__store']).get_cachekey()
                if saved:
                    self._set_qualitycheck_stats_cache(stats, key, timeout)

                saved = item['unit__store']
                stats = {}

            stats[item['name']] = item['count']

        if saved:
            self._set_qualitycheck_stats_cache(stats, key, timeout)

    def _set_wordcount_stats_cache(self, stats, key, timeout):
        if key:
            logging.info('Set wordcount stats for %s' % key)
            cache.set(key + ':get_total_wordcount', stats['total'], timeout)
            cache.set(key + ':get_fuzzy_wordcount', stats[FUZZY], timeout)
            cache.set(key + ':get_translated_wordcount', stats[TRANSLATED], timeout)

    def _set_wordcount_stats(self, timeout):
        res = Unit.objects.filter(state__gt=OBSOLETE) \
                            .values('store', 'state') \
                            .annotate(wordcount=Sum('source_wordcount')) \
                            .order_by('store', 'state')

        saved_id = None
        saved_key = None
        stats = None
        key = None

        for item in res:
            if saved_id != item['store']:
                key = Store.objects.get(id=item['store']).get_cachekey()
                if saved_key:
                    self._set_wordcount_stats_cache(stats, saved_key, timeout)

                stats = {'total': 0, FUZZY: 0, TRANSLATED: 0}
                saved_key = key
                saved_id = item['store']

            stats['total'] += item['wordcount']

            if item['state'] in [FUZZY, TRANSLATED]:
                stats[item['state']] = item['wordcount']

        if saved_id:
            self._set_wordcount_stats_cache(stats, key, timeout)

    def _set_empty_values(self, timeout):
        cache_values = {
            'get_last_action': {'id': 0 , 'mtime': 0, 'snippet': ''},
            'get_suggestion_count': 0,
            'get_checks': {},
            'get_total_wordcount': 0,
            'get_translated_wordcount': 0,
            'get_fuzzy_wordcount': 0
        }
        stores = Store.objects.all()
        for store in stores:
            key = store.get_cachekey()
            for func in cache_values:
                cache_key = iri_to_uri(key + ':' + func)
                cache.set(cache_key, cache_values[func], timeout)

        logging.info('Empty cache values were set for all stores.')

    def _set_last_action_stats(self, timeout):
        ss = Submission.simple_objects.values('unit__store__pootle_path') \
                                      .annotate(max_id=Max('id'))
        for s_id in ss:
            sub = Submission.objects.select_related('unit__store') \
                                    .get(id=s_id['max_id'])
            if sub.unit:
                key = iri_to_uri(sub.unit.store.get_cachekey() +
                                 ':get_last_action')
                logging.info('Set last action stats for %s' % key)
                res = {
                    'mtime': int(time.mktime(sub.unit.mtime.timetuple())),
                    'snippet': sub.get_submission_message()
                }
                cache.set(key, res, timeout)

        logging.info('All last actions were calculated.')

    def _set_suggestion_stats(self, timeout):
        """Check if any unit in the store has suggestions"""
        queryset = Suggestion.objects.filter(unit__state__gt=OBSOLETE) \
                                     .values('unit__store') \
                                     .annotate(count=Count('id'))

        for item in queryset:
            key = Store.objects.get(id=item['unit__store']).get_cachekey()
            logging.info('Set suggestion count for %s' % key)
            cache.set(key + ':get_suggestion_count', item['count'], timeout)

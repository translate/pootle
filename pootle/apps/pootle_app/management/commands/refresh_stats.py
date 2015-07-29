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
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from translate.filters.decorators import Category

from django.conf import settings
from django.core.urlresolvers import set_script_prefix
from django.db.models import Count, Max, Sum
from django.utils import dateformat, timezone
from django.utils.encoding import force_unicode, iri_to_uri

from django_rq import get_connection, job

from pootle.core.cache import get_cache
from pootle.core.mixins.treeitem import POOTLE_REFRESH_STATS
from pootle.core.utils.timezone import datetime_min
from pootle_project.models import Project
from pootle_statistics.models import Submission
from pootle_store.models import (Store, Unit, QualityCheck,
                                 Suggestion, SuggestionStates)
from pootle_store.util import OBSOLETE, UNTRANSLATED, FUZZY, TRANSLATED

from . import PootleCommand


logger = logging.getLogger('stats')
cache = get_cache('stats')


class Command(PootleCommand):
    help = "Allow stats and text indices to be refreshed manually."

    shared_option_list = (
        make_option('--calculate-checks', dest='calculate_checks',
                    action='store_true',
                    help='To recalculate quality checks for all strings'),
        make_option('--calculate-wordcount', dest='calculate_wordcount',
                    action='store_true',
                    help='To recalculate wordcount for all strings'),
        make_option('--check', action='append', dest='check_names',
                    help='Check to recalculate'),
    )

    option_list = PootleCommand.option_list + shared_option_list
    cached_methods = None
    process_disabled_projects = True

    def handle_noargs(self, **options):
        refresh_stats.delay(**options)
        option_list = map(lambda x: '%s=%s' % (x, options[x]),
                          filter(lambda x: options[x], options))
        self.stdout.write('refresh_stats RQ job added with options: %s. %s.' %
                          (', '.join(option_list),
                          'Please make sure rqworker is running'))

    def handle_all_stores(self, translation_project, **options):
        store_fk_filter = {
            'store__translation_project': translation_project,
        }
        unit_fk_filter = {
            'unit__store__translation_project': translation_project,
        }
        store_filter = {
            'translation_project': translation_project,
        }

        self.register_refresh_stats(translation_project.pootle_path)
        self.process(store_fk_filter=store_fk_filter,
                     unit_fk_filter=unit_fk_filter,
                     store_filter=store_filter,
                      **options)

        translation_project.refresh_stats(include_children=True,
                                          cached_methods=self.cached_methods)
        self.unregister_refresh_stats()
        translation_project.update_parent_cache()

    def handle_store(self, store, **options):
        store_fk_filter = {
            'store': store,
        }
        unit_fk_filter = {
            'unit__store': store,
        }
        store_filter = {
            'pk': store.pk,
        }

        self.register_refresh_stats(store.pootle_path)
        self.process(store_fk_filter=store_fk_filter,
                     unit_fk_filter=unit_fk_filter,
                     store_filter=store_filter,
                     **options)
        self.unregister_refresh_stats()
        store.update_parent_cache()

    def handle_all(self, **options):
        if not self.projects and not self.languages:
            logger.info(u"Running %s (noargs)", self.name)
            try:
                self.register_refresh_stats('/')

                self.process(**options)
                logger.info('Refreshing directories stats...')

                prj_query = Project.objects.all()

                for prj in prj_query.iterator():
                    # Calculate stats for all directories and translation projects
                    prj.refresh_stats(include_children=True,
                                      cached_methods=self.cached_methods)

                self.unregister_refresh_stats()
            except Exception:
                logger.exception(u"Failed to run %s", self.name)
        else:
            super(Command, self).handle_all(**options)

    def calculate_checks(self, check_names, unit_fk_filter, store_fk_filter):
        logger.info('Calculating quality checks for all units...')

        QualityCheck.delete_unknown_checks()

        checks = QualityCheck.objects.filter(**unit_fk_filter)
        if check_names:
            checks = checks.filter(name__in=check_names)
        checks = checks.values('id', 'name', 'unit_id',
                               'category', 'false_positive')
        all_units_checks = {}
        for check in checks:
            all_units_checks.setdefault(check['unit_id'], {})[check['name']] = check

        unit_count = 0
        units = Unit.simple_objects.select_related('store')
        units.query.clear_ordering(True)
        for unit in units.filter(**store_fk_filter).iterator():
            unit_count += 1
            unit_checks = {}
            if unit.id in all_units_checks:
                unit_checks = all_units_checks[unit.id]

            if unit.update_qualitychecks(keep_false_positives=True,
                                         check_names=check_names,
                                         existing=unit_checks):
                # update unit.mtime
                # TODO: add new action type `quality checks were updated`?
                Unit.simple_objects.filter(id=unit.id).update(mtime=timezone.now())

            if unit_count % 10000 == 0:
                logger.info("%d units processed" % unit_count)

    def process(self, **options):
        calculate_checks = options.get('calculate_checks', False)
        calculate_wordcount = options.get('calculate_wordcount', False)
        check_names = options.get('check_names', [])
        store_filter = options.get('store_filter', {})
        unit_fk_filter = options.get('unit_fk_filter', {})
        store_fk_filter = options.get('store_fk_filter', {})

        logger.info('Initializing stores...')

        stores = Store.objects.live()
        if store_filter:
            stores = stores.filter(**store_filter)

        self._init_stores(stores)
        # if check_names is non-empty then stats for only these checks
        # will be updated
        if not check_names:
            self._init_stats()
        self._init_checks()

        if calculate_checks:
            self.calculate_checks(check_names, unit_fk_filter, store_fk_filter)

        if calculate_wordcount:
            logger.info('Calculating wordcount for all units...')
            unit_count = 0
            for i, store in enumerate(stores.iterator(), start=1):
                logger.info("calculate wordcount for %s" % store.pootle_path)
                for unit in store.unit_set.iterator():
                    unit_count += 1
                    unit.update_wordcount()
                    unit.save()

                if i % 20 == 0:
                    logger.info("%d units processed" % unit_count)

        logger.info('Setting quality check stats values for all stores...')
        self._set_qualitycheck_stats(unit_fk_filter)

        if not check_names:
            logger.info('Setting last action values for all stores...')
            self._set_last_action_stats(store_fk_filter)
            logger.info('Setting last updated values for all stores...')
            self._set_last_updated_stats(store_fk_filter)
            logger.info('Setting mtime values for all stores...')
            self._set_mtime_stats(store_fk_filter)
            logger.info('Setting wordcount stats values for all stores...')
            self._set_wordcount_stats(store_fk_filter)
            logger.info('Setting suggestion count values for all stores...')
            self._set_suggestion_stats(unit_fk_filter)


        logger.info('Setting empty values for other cache entries...')
        self._set_empty_values()

    def _set_qualitycheck_stats_cache(self, stats, key):
        if key:
            logger.info('Set get_checks for %s' % key)
            cache.set(iri_to_uri(key + ':get_checks'), stats, None)
            del self.cache_values[key]['get_checks']

    def _set_qualitycheck_stats(self, check_filter):
        checks = QualityCheck.objects.filter(unit__state__gt=UNTRANSLATED,
                                               false_positive=False)
        if check_filter:
            checks = checks.filter(**check_filter)

        queryset = checks.values('unit', 'unit__store', 'name', 'category') \
                         .order_by('unit__store', 'unit', '-category')

        saved_store = None
        saved_unit = None
        stats = None

        for item in queryset.iterator():
            if item['unit__store'] != saved_store:
                try:
                    key = Store.objects.live().get(id=item['unit__store']) \
                                              .get_cachekey()
                except Store.DoesNotExist:
                    continue
                saved_store = item['unit__store']
                stats = self.cache_values[key]['get_checks']

            if item['name'] in stats['checks']:
                stats['checks'][item['name']] += 1
            else:
                stats['checks'][item['name']] = 1

            if saved_unit != item['unit']:
                saved_unit = item['unit']
                if item['category'] == Category.CRITICAL:
                    stats['unit_critical_error_count'] += 1

        for key in self.cache_values:
            stats = self.cache_values[key]['get_checks']
            if stats['unit_critical_error_count'] > 0:
                self._set_qualitycheck_stats_cache(stats, key)

    def _set_wordcount_stats_cache(self, stats, key):
        if key:
            logger.info('Set wordcount stats for %s' % key)
            cache.set(iri_to_uri(key + ':get_wordcount_stats'),
                      stats, None)

            del self.cache_values[key]['get_wordcount_stats']

    def _set_wordcount_stats(self, unit_filter):
        units = Unit.objects.filter(state__gt=OBSOLETE)
        if unit_filter:
            units = units.filter(**unit_filter)

        local_filetype = 'store__translation_project__project__localfiletype'
        res = units.values('store', 'state',
                           local_filetype,
                           'store__file') \
                   .annotate(wordcount=Sum('source_wordcount')) \
                   .order_by('store', 'state')

        saved_id = None
        saved_key = None
        stats = None
        key = None

        for item in res.iterator():
            # only include files with ext matching project ext
            file_ext = os.path.splitext(item['store__file'])[1][1:]
            proj_ext = item[
                'store__translation_project__project__localfiletype']
            if not file_ext == proj_ext:
                continue

            if saved_id != item['store']:
                try:
                    key = Store.objects.live().get(id=item['store']) \
                                              .get_cachekey()
                except Store.DoesNotExist:
                    continue

                if saved_key:
                    self._set_wordcount_stats_cache(stats, saved_key)

                stats = {'total': 0, 'fuzzy': 0, 'translated': 0}
                saved_key = key
                saved_id = item['store']

            stats['total'] += item['wordcount']

            if item['state'] == FUZZY:
                stats['fuzzy'] = item['wordcount']
            elif item['state'] == TRANSLATED:
                stats['translated'] = item['wordcount']

        if saved_id:
            self._set_wordcount_stats_cache(stats, key)

    def _init_stores(self, stores):
        self.cache_values = {}

        for store in stores.iterator():
            self.cache_values[store.get_cachekey()] = {}

    def _init_stats(self):
        for key in self.cache_values:
            self.cache_values[key].update({
                'get_last_action': {'id': 0, 'mtime': 0, 'snippet': ''},
                'get_suggestion_count': 0,
                'get_wordcount_stats': {'total': 0, 'fuzzy': 0, 'translated': 0},
                'get_mtime': datetime_min,
                'get_last_updated': {'id': 0, 'creation_time': 0,
                                     'snippet': ''},
            })

    def _init_checks(self):
        for key in self.cache_values:
            self.cache_values[key].update({
                'get_checks': {'unit_critical_error_count': 0,
                               'checks': {}},
            })

    def _set_empty_values(self):
        for key, value in self.cache_values.items():
            for func in value.keys():
                cache.set(iri_to_uri(key + ':' + func), value[func], None)

    def _set_last_action_stats(self, submission_filter):
        submissions = Submission.simple_objects
        if submission_filter:
            submissions = submissions.filter(**submission_filter)

        ss = submissions.values('store_id') \
                        .annotate(max_id=Max('id'))
        for s_id in ss.iterator():
            sub = Submission.objects.select_related('store') \
                                    .get(id=s_id['max_id'])

            if sub.unit and not sub.store.obsolete:
                sub_filter = {
                    'unit': sub.unit,
                    'creation_time': sub.creation_time,
                    'submitter': sub.submitter
                }
                sub = Submission.objects.select_related('store') \
                                        .filter(**sub_filter) \
                                        .order_by('field')[:1][0]
                key = sub.store.get_cachekey()
                logger.info('Set last action stats for %s' % key)
                res = {
                    'id': sub.unit.id,
                    'mtime': int(dateformat.format(sub.creation_time, 'U')),
                    'snippet': sub.get_submission_message()
                }
                cache.set(iri_to_uri(key + ':get_last_action'), res, None)
                del self.cache_values[key]['get_last_action']

    def _set_suggestion_stats(self, suggestion_filter):
        suggestions = Suggestion.objects.filter(
            unit__state__gt=OBSOLETE,
            state=SuggestionStates.PENDING,
        )
        if suggestion_filter:
            suggestions = suggestions.filter(**suggestion_filter)

        queryset = suggestions \
            .values('unit__store').annotate(count=Count('id'))

        for item in queryset.iterator():
            try:
                key = Store.objects.live().get(id=item['unit__store']) \
                                          .get_cachekey()
            except Store.DoesNotExist:
                continue
            logger.info('Set suggestion count for %s' % key)
            cache.set(iri_to_uri(key + ':get_suggestion_count'),
                      item['count'], None)
            del self.cache_values[key]['get_suggestion_count']

    def _set_mtime_stats(self, unit_filter):
        units = Unit.objects.all()
        if unit_filter:
            units = units.filter(**unit_filter)

        queryset = units.values('store').annotate(
            max_mtime=Max('mtime')
        )

        for item in queryset.iterator():
            try:
                key = Store.objects.live().get(id=item['store']).get_cachekey()
            except Store.DoesNotExist:
                continue
            logger.info('Set mtime for %s' % key)
            cache.set(iri_to_uri(key + ':get_mtime'),
                      item['max_mtime'], None)
            del self.cache_values[key]['get_mtime']

    def _set_last_updated_stats(self, unit_filter):
        units = Unit.objects.all()
        if unit_filter:
            units = units.filter(**unit_filter)

        queryset = units.values('store').annotate(
            max_creation_time=Max('creation_time')
        )

        for item in queryset.iterator():
            max_time = item['max_creation_time']
            if max_time:
                try:
                    store = Store.objects.live().get(id=item['store'])
                except Store.DoesNotExist:
                    continue
                unit = store.unit_set.filter(creation_time=max_time)[0]
                key = store.get_cachekey()
                logger.info('Set last_updated for %s' % key)
                res = {
                    'id': unit.id,
                    'creation_time': int(dateformat.format(max_time, 'U')),
                    'snippet': unit.get_last_updated_message()
                }
                cache.set(iri_to_uri(key + ':get_last_updated'), res, None)
                del self.cache_values[key]['get_last_updated']

    def register_refresh_stats(self, path):
        """Register that stats for current path is going to be refreshed"""
        r_con = get_connection()
        r_con.set(POOTLE_REFRESH_STATS, path)

    def unregister_refresh_stats(self):
        """Unregister current path when stats for this path were refreshed"""
        r_con = get_connection()
        r_con.delete(POOTLE_REFRESH_STATS)


@job('default', timeout=18000)
def refresh_stats(**options):
    # The script prefix needs to be set here because the generated
    # URLs need to be aware of that and they are cached. Ideally
    # Django should take care of setting this up, but it doesn't yet:
    # https://code.djangoproject.com/ticket/16734
    script_name = (u'/' if settings.FORCE_SCRIPT_NAME is None
                        else force_unicode(settings.FORCE_SCRIPT_NAME))
    set_script_prefix(script_name)
    super(Command, Command()).handle_noargs(**options)

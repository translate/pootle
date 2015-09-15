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

from django.utils import timezone

from pootle.core.mixins.treeitem import CachedMethods
from pootle_store.models import Store, QualityCheck, Unit
from pootle_store.util import OBSOLETE

from . import PootleCommand


class Command(PootleCommand):
    help = "Allow checks to be recalculated manually."

    shared_option_list = (
        make_option('--check', action='append', dest='check_names',
                    help='Check to recalculate'),
    )

    cached_methods = [CachedMethods.CHECKS]
    process_disabled_projects = True

    def handle_all_stores(self, translation_project, **options):
        check_names = options.get('check_names', None)
        calculate_checks(check_names=check_names,
                         translation_project=translation_project)

    def handle_all(self, **options):
        if not self.projects and not self.languages:
            logging.info(u"Running %s (noargs)", self.name)

            check_names = options.get('check_names', None)
            translation_project = options.get('translation_project', None)
            try:

                calculate_checks(check_names=check_names,
                                 translation_project=translation_project)
            except Exception:
                logging.exception(u"Failed to run %s", self.name)
        else:
            super(Command, self).handle_all(**options)


def calculate_checks(check_names=None, translation_project=None):
    store_fk_filter = {}
    unit_fk_filter = {}

    if translation_project is not None:
        store_fk_filter = {
            'store__translation_project': translation_project,
        }
        unit_fk_filter = {
            'unit__store__translation_project': translation_project,
        }

    logging.info('Calculating quality checks for all units...')
    QualityCheck.delete_unknown_checks()

    checks = QualityCheck.objects.filter(**unit_fk_filter)
    if check_names is not None:
        checks = checks.filter(name__in=check_names)
    checks = checks.values('id', 'name', 'unit_id',
                           'category', 'false_positive')
    all_units_checks = {}
    for check in checks:
        all_units_checks.setdefault(check['unit_id'], {})[check['name']] = check

    unit_filter = {
        'state__gt': OBSOLETE
    }
    unit_filter.update(store_fk_filter)
    # unit's query is faster without `select_related('store')`
    units = Unit.simple_objects.filter(**unit_filter) \
                               .order_by('store__id')
    store = None
    # units are ordered by store, we update dirty cache after we switch
    # to another store
    for unit_count, unit in enumerate(units.iterator(), start=1):
        if store is None or unit.store_id != store.id:
            if store is not None:
                store.update_dirty_cache()
            # we get unit.store only if the store differs from previous
            store = Store.simple_objects.get(id=unit.store_id)

        # HACKISH: set unit.store to avoid extra querying in
        # `unit.update_quality_checks()` method
        unit.store = store

        unit_checks = {}
        if unit.id in all_units_checks:
            unit_checks = all_units_checks[unit.id]

        if unit.update_qualitychecks(keep_false_positives=True,
                                     check_names=check_names,
                                     existing=unit_checks):

            # update unit.mtime but avoid to use unit.save()
            # because it can trigger unnecessary things:
            # logging, stats cache updating
            # TODO: add new action type `quality checks were updated`?
            Unit.simple_objects.filter(id=unit.id).update(mtime=timezone.now())

        if unit_count % 10000 == 0:
            logging.info("%d units processed" % unit_count)

    if store is not None:
        store.update_dirty_cache()

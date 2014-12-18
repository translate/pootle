#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
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

import logging
import os
from optparse import make_option

# This must be run before importing Django.
os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'

from django.conf import settings
from django.core.cache import get_cache, cache as default_cache
from django.core.exceptions import ImproperlyConfigured
from django.core.urlresolvers import set_script_prefix
from django.utils.encoding import force_unicode

from django_rq import job

from pootle.core.mixins.treeitem import CachedMethods
from pootle_store.models import Store

from .refresh_stats import Command as RefreshStatsCommand


logger = logging.getLogger('stats')

try:
    cache = get_cache('stats')
except ImproperlyConfigured:
    cache = default_cache


class Command(RefreshStatsCommand):
    help = "Allow stats and text indices to be refreshed manually."

    shared_option_list = (
        make_option('--check', action='append', dest='check_names',
                    help='Check to recalculate'),
    )
    cached_methods = [CachedMethods.CHECKS]

    def handle_noargs(self, **options):
        calculate_checks.delay(**options)
        option_list = map(lambda x: '%s=%s' % (x, options[x]),
                          filter(lambda x: options[x], options))
        self.stdout.write('calculate checks RQ job added with options: %s. %s.' %
                          (', '.join(option_list),
                          'Please make sure rqworker is running'))

    def process(self, **options):
        check_names = options.get('check_names', [])
        store_filter = options.get('store_filter', {})
        unit_fk_filter = options.get('unit_fk_filter', {})
        store_fk_filter = options.get('store_fk_filter', {})

        logger.info('Initializing stores...')

        stores = Store.objects.all()
        if store_filter:
            stores = stores.filter(**store_filter)

        self._init_stores(stores)
        self._init_checks()
        self.calculate_checks(check_names, unit_fk_filter, store_fk_filter)

        logger.info('Setting quality check stats values for all stores...')
        self._set_qualitycheck_stats(unit_fk_filter)
        logger.info('Setting empty values for other cache entries...')
        self._set_empty_values()


@job('default', timeout=18000)
def calculate_checks(**options):
    # The script prefix needs to be set here because the generated
    # URLs need to be aware of that and they are cached. Ideally
    # Django should take care of setting this up, but it doesn't yet:
    # https://code.djangoproject.com/ticket/16734
    script_name = (u'/' if settings.FORCE_SCRIPT_NAME is None
                        else force_unicode(settings.FORCE_SCRIPT_NAME))
    set_script_prefix(script_name)
    super(RefreshStatsCommand, Command()).handle_noargs(**options)

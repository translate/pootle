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

#from django.core.management.base import NoArgsCommand
from pootle_app.management.commands import PootleCommand

from django.db.models import Max
from django.utils.encoding import iri_to_uri
from django.core.cache import cache
from django.conf import settings

from pootle_statistics.models import Submission


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
        timeout=settings.OBJECT_CACHE_TIMEOUT

        ss = Submission.simple_objects.values('unit__store__pootle_path').annotate(max_id=Max('id'))
        for s_id in ss:
            sub = Submission.objects.select_related('unit__store').get(id=s_id['max_id'])
            if sub.unit:
                key = iri_to_uri(sub.unit.store.get_cachekey() + ":" + 'get_last_action')
                logging.info(key)
                res = {
                    'mtime': int(time.mktime(sub.unit.mtime.timetuple())),
                    'snippet': sub.get_submission_message()
                }
                cache.set(key, res, timeout)

        # info finish
        end = datetime.datetime.now()
        logging.info('All done for %s in %s', self.name, end - start)


    def get_total_wordcount(self):
        pass
    def get_translated_wordcount(self):
        pass
    def get_fuzzy_wordcount(self):
        pass
    def get_suggestion_count(self):
        pass
    def get_last_action(self):
        pass
    def get_mtime(self):
        pass
    def get_checks(self):
        pass

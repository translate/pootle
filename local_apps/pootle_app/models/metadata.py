#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2009 Zuza Software Foundation
# 
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.conf import settings

import logging
import traceback

from translate.storage import statsdb

import store_iteration

def add_to_stats(stats, other_stats):
    for key, value in other_stats.iteritems():
        stats[key] = stats.get(key, 0) + value

def get_stats_cache():
    return statsdb.StatsCache(settings.STATS_DB_PATH)

def num_stores(path_obj, search=None):
    if path_obj.is_dir:
        return sum(1 for x in store_iteration.iter_stores(path_obj, search=search))
    else:
        return 1

def stats_totals(path_obj, checker, search=None):
    if path_obj.is_dir:
        result = statsdb.emptyfiletotals()
        for store in store_iteration.iter_stores(path_obj, search=search):
            add_to_stats(result, stats_totals(store, checker, search))
        return result
    else:
        def compute_lengths(full_stats):
            return dict((key, len(value)) for key, value in full_stats.iteritems())

        totals = quick_stats(path_obj, checker)
        totals.update(compute_lengths(property_stats(path_obj, checker)))
        return totals

def quick_stats(path_obj, checker, search=None):
    if path_obj.is_dir:
        result = statsdb.emptyfiletotals()
        for store in store_iteration.iter_stores(path_obj, search=search):
            add_to_stats(result, quick_stats(store, checker))
        return result
    else:
        return path_obj.file.getquickstats() #or statsdb.emptyfiletotals()


def property_stats(path_obj, checker, *args):
    try:
        return path_obj.file.getcompletestats(checker) or \
            statsdb.emptyfilestats()
    except:
        logging.log(logging.ERROR, traceback.format_exc())
        return statsdb.emptyfilestats()

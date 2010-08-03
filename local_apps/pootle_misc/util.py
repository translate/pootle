#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2009 Zuza Software Foundation
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

from django.core.cache import cache
from django.conf import settings
from django.core.paginator import Paginator
from django.utils.encoding import iri_to_uri

def getfromcache(function, timeout=settings.OBJECT_CACHE_TIMEOUT):
    def _getfromcache(instance, *args, **kwargs):
        key = iri_to_uri(instance.pootle_path + ":" + function.__name__)
        result = cache.get(key)
        if result is None:
            logging.debug("cache miss for %s", key)
            result = function(instance, *args, **kwargs)
            cache.set(key, result, timeout)
        return result
    return _getfromcache

def deletefromcache(sender, functions, **kwargs):
    path = iri_to_uri(sender.pootle_path)
    path_parts = path.split("/")

    # clean project cache
    if len(path_parts):
        key = "/projects/%s/" % path_parts[2]
        for func in functions:
            cache.delete(key + ":"+func)

    # clean store and directory cache
    while path_parts:
        for func in functions:
            cache.delete(path + ":"+func)
        path_parts = path_parts[:-1]
        path = "/".join(path_parts) + "/"

def dictsum(x, y):
    return dict( (n, x.get(n, 0)+y.get(n, 0)) for n in set(x)|set(y) )


def paginate(request, queryset, items=30, page=None):
    paginator = Paginator(queryset, items, orphans=items/2)

    if not page:
        try:
            page = int(request.GET.get('page', 1))
        except ValueError:
            # wasn't an int use 1
            page = 1
    # page value too large
    page = min(page, paginator.num_pages)

    return paginator.page(page)

def nice_percentage(percentage):
    """Return an integer percentage, but avoid returning 0% or 100% if it
    might be misleading."""
    # Let's try to be clever and make sure than anything above 0.0 and below 0.5
    # will show as at least 1%, and anything above 99.5% and less than 100% will
    # show as 99%.
    if 99 < percentage < 100:
        return 99
    if 0 < percentage < 1:
        return 1
    return int(round(percentage))

def add_percentages(quick_stats):
    """Add percentages onto the raw stats dictionary."""
    quick_stats['translatedpercentage'] = nice_percentage(100.0 * quick_stats['translatedsourcewords'] / max(quick_stats['totalsourcewords'], 1))
    quick_stats['fuzzypercentage'] = nice_percentage(100.0 * quick_stats['fuzzysourcewords'] / max(quick_stats['totalsourcewords'], 1))
    quick_stats['untranslatedpercentage'] = 100 - quick_stats['translatedpercentage'] - quick_stats['fuzzypercentage']
    quick_stats['strtranslatedpercentage'] = nice_percentage(100.0 * quick_stats['translated'] / max(quick_stats['total'], 1))
    quick_stats['strfuzzypercentage'] = nice_percentage(100.0 * quick_stats['fuzzy'] / max(quick_stats['total'], 1))
    quick_stats['struntranslatedpercentage'] = 100 - quick_stats['strtranslatedpercentage'] - quick_stats['strfuzzypercentage']

    return quick_stats

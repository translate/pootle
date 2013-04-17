#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2013 Zuza Software Foundation
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

from django.conf import settings
from django.core.cache import cache
from django.core.paginator import Paginator
from django.http import HttpResponseBadRequest
from django.utils import simplejson
from django.utils.encoding import force_unicode, iri_to_uri
from django.utils.functional import Promise

from pootle.core.markup import Markup

# We host a copy of the timezone helpers in Django 1.4+ for the sake of Django
# 1.3:
try:
    from django.utils import tzinfo
    from django.utils import timezone
except ImportError:
    from pootle_misc import tzinfo
    from pootle_misc import timezone


# Timezone aware minimum for datetime (if appropriate) (bug 2567)
from datetime import datetime
datetime_min = datetime.min
if settings.USE_TZ:
    datetime_min = timezone.make_aware(datetime_min, timezone.utc)

from translate.misc.decorators import decorate


def getfromcache(function, timeout=settings.OBJECT_CACHE_TIMEOUT):
    def _getfromcache(instance, *args, **kwargs):
        key = iri_to_uri(instance.pootle_path + ":" + function.__name__)
        result = cache.get(key)
        if result is None:
            logging.debug(u"cache miss for %s", key)
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
            cache.delete(key + ":" + func)

    # clean store and directory cache
    while path_parts:
        for func in functions:
            cache.delete(path + ":" + func)

        path_parts = path_parts[:-1]
        path = "/".join(path_parts) + "/"


def dictsum(x, y):
    return dict((n, x.get(n, 0)+y.get(n, 0)) for n in set(x) | set(y))


def paginate(request, queryset, items=30, page=None):
    paginator = Paginator(queryset, items)

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


class PootleJSONEncoder(simplejson.JSONEncoder):
    """Custom JSON encoder for Pootle.

    This is mostly implemented to avoid calling `force_unicode` all the
    time on certain types of objects.
    https://docs.djangoproject.com/en/1.4/topics/serialization/#id2
    """

    def default(self, obj):
        if isinstance(obj, Promise) or isinstance(obj, Markup):
            return force_unicode(obj)

        return super(PootleEncoder, self).default(obj)


def jsonify(obj):
    """Serialize Python `obj` object into a JSON string."""
    if settings.DEBUG:
        indent = 4
    else:
        indent = None

    return simplejson.dumps(obj, indent=indent, cls=PootleJSONEncoder)


@decorate
def ajax_required(f):
    """
    AJAX request required decorator
    use it in your views:

    @ajax_required
    def my_view(request):
        ....

    Taken from:
    http://djangosnippets.org/snippets/771/
    """
    def wrapper(request, *args, **kwargs):
        if not settings.DEBUG and not request.is_ajax():
            return HttpResponseBadRequest("This must be an AJAX request.")
        return f(request, *args, **kwargs)

    return wrapper


def cached_property(f):
    """A property which value is computed only once and then stored with
    the instance for quick repeated retrieval.
    """

    def _closure(self):
        cache_key = '_cache__%s' % f.__name__
        value = getattr(self, cache_key, None)

        if value is None:
            value = f(self)
            setattr(self, cache_key, value)

        return value

    return property(_closure)

#!/usr/bin/python
# -*- coding: utf-8 -*-
#
# Copyright 2004-2006 Zuza Software Foundation
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

import os

from django.conf import settings
from django.http import HttpResponseBadRequest

from pootle_misc.aggregate import sum_column
from pootle_misc.util import dictsum

# Unit States
OBSOLETE = -100
"""unit is no longer part of store"""
UNTRANSLATED = 0
"""empty unit"""
FUZZY = 50
"""marked as fuzzy, typically means translation needs more work"""
TRANSLATED = 200
"""unit is fully translated"""

def add_trailing_slash(path):
    """If path does not end with /, add it and return."""

    if path[-1] == os.sep:
        return path
    else:
        return path + os.sep


def relative_real_path(p):
    if p.startswith(settings.PODIRECTORY):
        return p[len(add_trailing_slash(settings.PODIRECTORY)):]
    else:
        return p


def absolute_real_path(p):
    if not p.startswith(settings.PODIRECTORY):
        return os.path.join(settings.PODIRECTORY, p)
    else:
        return p


empty_quickstats = {'fuzzy': 0,
                    'fuzzysourcewords': 0,
                    'review': 0,
                    'total': 0,
                    'totalsourcewords': 0,
                    'translated': 0,
                    'translatedsourcewords': 0,
                    'translatedtargetwords': 0,
                    'untranslated': 0,
                    'untranslatedsourcewords': 0,
                    'errors': 0}

def statssum(queryset, empty_stats=empty_quickstats):
    totals = empty_stats
    for item in queryset:
        try:
            totals = dictsum(totals, item.getquickstats())
        except:
            totals['errors'] += 1
    return totals

empty_completestats = {u'isfuzzy': 0,
                       'errors': 0}

def completestatssum(queryset, empty_stats=empty_completestats):
    totals = empty_stats
    for item in queryset:
        try:
            totals = dictsum(totals, item.getcompletestats())
        except:
            totals['errors'] += 1
    return totals

def calculate_stats(units):
    """calculate translation statistics for given unit queryset"""
    total = sum_column(units,
                       ['source_wordcount'], count=True)
    untranslated = sum_column(units.filter(state=UNTRANSLATED),
                              ['source_wordcount'], count=True)
    fuzzy = sum_column(units.filter(state=FUZZY),
                       ['source_wordcount'], count=True)
    translated = sum_column(units.filter(state=TRANSLATED),
                            ['source_wordcount', 'target_wordcount'], count=True)
    result = {}
    result['total'] = total['count']
    if result['total'] == 0:
        result['totalsourcewords'] = 0
    else:
        result['totalsourcewords'] = total['source_wordcount']
    result['fuzzy'] = fuzzy['count']
    if result['fuzzy'] == 0:
        result['fuzzysourcewords'] = 0
    else:
        result['fuzzysourcewords'] = fuzzy['source_wordcount']
    result['untranslated'] = untranslated['count']
    if result['untranslated'] == 0:
        result['untranslatedsourcewords'] = 0
    else:
        result['untranslatedsourcewords'] = untranslated['source_wordcount']
    result['translated'] = translated['count']
    if result['translated'] == 0:
        result['translatedsourcewords'] = 0
        result['translatedtargetwords'] = 0
    else:
        result['translatedsourcewords'] = translated['source_wordcount']
        result['translatedtargetwords'] = translated['target_wordcount']
    return result

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
        if not request.is_ajax():
            return HttpResponseBadRequest("This must be an AJAX request.")
        return f(request, *args, **kwargs)
    return wrapper

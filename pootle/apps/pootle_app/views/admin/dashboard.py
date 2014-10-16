#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2014 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import json
import locale
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext as _

from pootle.core.diagnostics import depcheck
from pootle.core.decorators import admin_required
from pootle.core.markup import get_markup_filter
from pootle_misc.aggregate import sum_column
from pootle_statistics.models import Submission
from pootle_store.models import Suggestion, Unit
from pootle_store.util import TRANSLATED


User = get_user_model()


def _format_numbers(dict):
    for k in dict.keys():
        formatted_number = locale.format("%d", dict[k], grouping=True)
        # Under Windows, formatted number must be converted to Unicode
        if os.name == 'nt':
            formatted_number = formatted_number.decode(
                locale.getpreferredencoding()
            )
        dict[k] = formatted_number


def server_stats():
    result = cache.get("server_stats")
    if result is None:
        result = {}
        result['user_count'] = max(User.objects.filter(is_active=True).count()-2, 0)
        # 'default' and 'nobody' might be counted
        # FIXME: the special users should not be retuned with is_active
        result['submission_count'] = Submission.objects.count()
        result['pending_count'] = Suggestion.objects.pending().count()
        cache.set("server_stats", result, 86400)
    _format_numbers(result)
    return result


@admin_required
def server_stats_more(request):
    result = cache.get("server_stats_more")
    if result is None:
        result = {}
        unit_query = Unit.objects.filter(state__gte=TRANSLATED).exclude(
            store__translation_project__project__code__in=('pootle', 'tutorial', 'terminology')).exclude(
            store__translation_project__language__code='templates').order_by()
        result['store_count'] = unit_query.values('store').distinct().count()
        result['project_count'] = unit_query.values('store__translation_project__project').distinct().count()
        result['language_count'] = unit_query.values('store__translation_project__language').distinct().count()
        sums = sum_column(unit_query, ('source_wordcount',), count=True)
        result['string_count'] = sums['count']
        result['word_count'] = sums['source_wordcount'] or 0
        result['user_active_count'] = (
            User.objects.exclude(submission=None) |
            User.objects.exclude(suggestions=None)
        ).order_by().count()
        cache.set("server_stats_more", result, 86400)
    _format_numbers(result)
    stat_strings = {
        'store_count': _('Files'),
        'project_count': _('Active projects'),
        'language_count': _('Active languages'),
        'string_count': _('Translated strings'),
        'word_count': _('Translated words'),
        'user_active_count': _('Active users')
    }
    response = []
    for k in result.keys():
        response.append((stat_strings[k], result[k]))
    response = json.dumps(response)
    return HttpResponse(response, content_type="application/json")


@admin_required
def view(request):
    ctx = {
        'server_stats': server_stats(),
        'required': depcheck.check_required(),
        'optional': depcheck.check_optional(),
        'optimal': depcheck.check_optimal(),
    }
    return render(request, "admin/dashboard.html", ctx)

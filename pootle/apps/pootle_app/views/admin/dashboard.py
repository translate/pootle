#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
import locale
import os

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.http import HttpResponse
from django.shortcuts import render
from django.utils.translation import ugettext as _, ungettext

from django_rq.queues import get_queue, get_failed_queue
from django_rq.workers import Worker
from redis.exceptions import ConnectionError

from pootle import depcheck
from pootle.core.decorators import admin_required
from pootle.core.markup import get_markup_filter
from pootle_misc.aggregate import sum_column
from pootle_statistics.models import Submission
from pootle_store.models import Unit, Suggestion
from pootle_store.util import TRANSLATED


def optional_depcheck():
    optional = []

    if not depcheck.test_iso_codes():
        optional.append({
            'dependency': 'iso-codes',
            'text': _("Can't find the ISO codes package. Pootle uses ISO codes"
                      " to translate language names.")
        })
    if not depcheck.test_levenshtein():
        optional.append({
            'dependency': 'levenshtein',
            'text': _("Can't find python-levenshtein package. Updating against"
                      " templates is faster with python-levenshtein.")
        })

    filter_name, filter_args = get_markup_filter()
    if filter_name is None:
        text = None
        if filter_args == 'missing':
            text = _("MARKUP_FILTER is missing. Falling back to HTML.")
        elif filter_args == 'misconfigured':
            text = _("MARKUP_FILTER is misconfigured. Falling back to HTML.")
        elif filter_args == 'uninstalled':
            text = _("Can't find the package which provides '%s' markup "
                     "support. Falling back to HTML.",
                     settings.MARKUP_FILTER[0])
        elif filter_args == 'invalid':
            text = _("Invalid value '%s' in MARKUP_FILTER. Falling back to "
                     "HTML.", settings.MARKUP_FILTER[0])

        if text is not None:
            optional.append({
                'dependency': filter_args + '-markup',
                'text': text
            })

    return optional


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
    User = get_user_model()
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
        User = get_user_model()

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


def rq_stats():
    queue = get_queue()
    failed_queue = get_failed_queue()
    try:
        workers = Worker.all(queue.connection)
    except ConnectionError:
        return None
    is_running = False
    if len(workers) == 1:
        is_running = not workers[0].stopped

    result = {
        'job_count': queue.count,
        'failed_job_count': failed_queue.count,
        'is_running': is_running,
    }

    return result


@admin_required
def view(request):
    ctx = {
        'server_stats': server_stats(),
        'rq_stats': rq_stats(),
        'required': {},
        'optional': optional_depcheck(),
        'optimal': {},
    }
    return render(request, "admin/dashboard.html", ctx)

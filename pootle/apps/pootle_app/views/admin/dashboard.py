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

from pootle import depcheck
from pootle.core.decorators import admin_required
from pootle.core.markup import get_markup_filter
from pootle_misc.aggregate import sum_column
from pootle_statistics.models import Submission
from pootle_store.models import Suggestion, Unit
from pootle_store.util import TRANSLATED


User = get_user_model()


def required_depcheck():
    required = []

    status, version = depcheck.test_translate()
    if status:
        text = _('Translate Toolkit version %s installed.', version)
        state = 'tick'
    else:
        trans_vars = {
            'installed': version,
            'required': ".".join([str(i) for i in
                                  depcheck.TTK_MINIMUM_REQUIRED_VERSION]),
        }
        text = _("Translate Toolkit version %(installed)s installed. Pootle "
                 "requires at least version %(required)s.", trans_vars)
        state = 'error'

    required.append({
        'dependency': 'translate',
        'state': state,
        'text': text,
    })

    status, version = depcheck.test_django()
    if status:
        text = _('Django version %s is installed.', version)
        state = 'tick'
    else:
        trans_vars = {
            'installed': version,
            'required': ".".join([str(i) for i in
                                  depcheck.DJANGO_MINIMUM_REQUIRED_VERSION]),
        }
        text = _("Django version %(installed)s is installed. Pootle requires "
                 "at least version %(required)s.", trans_vars)
        state = 'error'

    required.append({
        'dependency': 'django',
        'state': state,
        'text': text,
    })

    status, version = depcheck.test_lxml()
    if status:
        text = _('lxml version %s is installed.', version)
        state = 'tick'
    elif version is not None:
        trans_vars = {
            'installed': version,
            'required': ".".join([str(i) for i in
                                  depcheck.LXML_MINIMUM_REQUIRED_VERSION]),
        }
        text = _("lxml version %(installed)s is installed. Pootle requires at "
                 "least version %(required)s.", trans_vars)
        state = 'error'
    else:
        text = _('lxml is not installed. Pootle requires lxml.')
        state = 'error'

    required.append({
        'dependency': 'lxml',
        'state': state,
        'text': text,
    })

    return required


def optional_depcheck():
    optional = []

    if not depcheck.test_unzip():
        optional.append({
            'dependency': 'unzip',
            'text': _('Can\'t find the unzip command. Uploading archives is '
                      'faster if "unzip" is available.')
        })
    if not depcheck.test_iso_codes():
        optional.append({
            'dependency': 'iso-codes',
            'text': _("Can't find the ISO codes package. Pootle uses ISO codes"
                      " to translate language names.")
        })
    if not depcheck.test_gaupol():
        optional.append({
            'dependency': 'gaupol',
            'text': _("Can't find the aeidon package. Pootle requires Gaupol "
                      "or aeidon to support subtitle formats.")
        })
    if not depcheck.test_levenshtein():
        optional.append({
            'dependency': 'levenshtein',
            'text': _("Can't find python-levenshtein package. Updating against"
                      " templates is faster with python-levenshtein.")
        })
    if not depcheck.test_indexer():
        optional.append({
            'dependency': 'indexer',
            'text': _("No text indexing engine found. Searching is faster if "
                      "an indexing engine like Xapian or Lucene is installed.")
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


def optimal_depcheck():
    optimal = []

    if not depcheck.test_db():
        if depcheck.test_mysqldb():
            text = _("Using the default sqlite3 database engine. SQLite is "
                     "only suitable for small installations with a small "
                     "number of users. Pootle will perform better with the "
                     "MySQL database engine.")
        else:
            text = _("Using the default sqlite3 database engine. SQLite is "
                     "only suitable for small installations with a small "
                     "number of users. Pootle will perform better with the "
                     "MySQL database engine, but you need to install "
                     "python-MySQLdb first.")
        optimal.append({'dependency': 'db', 'text': text})

    if depcheck.test_cache():
        if depcheck.test_memcache():
            if not depcheck.test_memcached():
                # memcached configured but connection failing
                optimal.append({
                    'dependency': 'cache',
                    'text': _("Pootle is configured to use memcached as a "
                              "caching backend, but can't connect to the "
                              "memcached server. Caching is currently "
                              "disabled.")
                })
            else:
                if not depcheck.test_session():
                    text = _("For optimal performance, use django.contrib."
                             "sessions.backends.cached_db as the session "
                             "engine.")
                    optimal.append({'dependency': 'session', 'text': text})
        else:
            optimal.append({
                'dependency': 'cache',
                'text': _("Pootle is configured to use memcached as caching "
                          "backend, but Python support for memcached is not "
                          "installed. Caching is currently disabled.")
            })
    else:
        optimal.append({
            'dependency': 'cache',
            'text': _("For optimal performance, use memcached as the caching "
                      "backend.")
        })

    if not depcheck.test_webserver():
        optimal.append({
            'dependency': 'webserver',
            'text': _("For optimal performance, use Apache as the webserver.")
        })
    if not depcheck.test_from_email():
        optimal.append({
            'dependency': 'from_email',
            'text': _('The "from" address used to send registration emails is '
                      'not specified. Also review the mail server settings.')
        })
    if not depcheck.test_contact_email():
        optimal.append({
            'dependency': 'contact_email',
            'text': _("No contact address is specified. The contact form will "
                      "allow users to contact the server administrators.")
        })
    if not depcheck.test_debug():
        optimal.append({
            'dependency': 'debug',
            'text': _("Running in debug mode. Debug mode is only needed when "
                      "developing Pootle. For optimal performance, disable "
                      "debugging mode.")
        })

    return optimal


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
        'required': required_depcheck(),
        'optional': optional_depcheck(),
        'optimal': optimal_depcheck(),
    }
    return render(request, "admin/dashboard.html", ctx)

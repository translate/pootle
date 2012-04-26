#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

import locale

from django.http import HttpResponse
from django.utils.translation import ugettext as _
from django.shortcuts import render_to_response
from django.template import RequestContext
from django.core.cache import cache
from django.utils import simplejson

from django.contrib.auth.models import User

from pootle import depcheck

from pootle_app.views.admin.util import user_is_admin
from pootle_misc.aggregate import sum_column
from pootle_app.models import Suggestion as SuggestionStat
from pootle_store.models import Unit, Suggestion
from pootle_profile.models import PootleProfile
from pootle_store.util import TRANSLATED
from pootle_statistics.models import Submission

def required_depcheck():
    required = []

    status, version = depcheck.test_translate()
    if status:
        text = _('Translate Toolkit version %s installed.', version)
        state = 'good'
    else:
        text = _('Translate Toolkit version %(installed)s installed. Pootle requires at least version %(required)s.', {'installed': version, 'required': ".".join(depcheck.translate_required_ver)})
        state = 'error'
    required.append({'dependency': 'translate', 'state': state, 'text': text})

    status, version = depcheck.test_django()
    if status:
        text = _('Django version %s is installed.', version)
        state = 'good'
    else:
        text = _('Django version %s is installed, but a higher version is highly recommended.', version)
        state = 'error'
    required.append({'dependency': 'django', 'state': state, 'text': text})

    status, version = depcheck.test_lxml()
    if status:
        text = _('lxml version %s is installed.', version)
        state = 'good'
    elif version is not None:
        text = _('lxml version %(installed)s is installed. Pootle requires at least version %(required)s for XML format support.', {'installed': version, 'required': ".".join(depcheck.lxml_required_ver)})
        state = 'error'
    else:
        text = _('lxml is not installed. Pootle requires lxml for XML format support.')
        state = 'error'
    required.append({'dependency': 'lxml', 'state': state, 'text': text})
    return required


def optional_depcheck():
    optional = []

    if not depcheck.test_unzip():
        optional.append({'dependency': 'unzip',
                         'text': _('Can\'t find the unzip command. Uploading archives is faster if "unzip" is available.')})

    if not depcheck.test_iso_codes():
        optional.append({'dependency': 'iso-codes',
                           'text': _("Can't find the ISO codes package. Pootle uses ISO codes to translate language names.")})

    if not depcheck.test_gaupol():
        optional.append({'dependency': 'gaupol',
                         'text': _("Can't find the aeidon package. Pootle requires Gaupol or aeidon to support subtitle formats.")})

    if not depcheck.test_levenshtein():
        optional.append({'dependency': 'levenshtein',
                        'text': _("Can't find python-levenshtein package. Updating from templates is faster with python-levenshtein.")})

    if not depcheck.test_indexer():
        optional.append({'dependency': 'indexer',
                         'text': _("No text indexing engine found. Searching is faster if an indexing engine like Xapian or Lucene is installed.")})

    return optional


def optimal_depcheck():
    optimal = []

    if not depcheck.test_db():
        if depcheck.test_mysqldb():
            text = _("Using the default sqlite3 database engine. SQLite is only suitable for small installations with a small number of users. Pootle will perform better with the MySQL database engine.")
        else:
            text = _("Using the default sqlite3 database engine. SQLite is only suitable for small installations with a small number of users. Pootle will perform better with the MySQL database engine, but you need to install python-MySQLdb first.")
        optimal.append({'dependency': 'db', 'text': text})

    if depcheck.test_cache():
        if depcheck.test_memcache():
            if not depcheck.test_memcached():
                # memcached configured but connection failing
                optimal.append({'dependency': 'cache',
                                'text': _("Pootle is configured to use memcached as a caching backend, but can't connect to the memcached server. Caching is currently disabled.")})
            else:
                if not depcheck.test_session():
                    text = _('For optimal performance, use django.contrib.sessions.backends.cached_db as the session engine.')
                    optimal.append({'dependency': 'session', 'text': text})
        else:
            optimal.append({'dependency': 'cache',
                            'text': _('Pootle is configured to use memcached as caching backend, but Python support for memcached is not installed. Caching is currently disabled.')})
    else:
        optimal.append({'dependency': 'cache',
                        'text': _('For optimal performance, use memcached as the caching backend.')})

    if not depcheck.test_webserver():
        optimal.append({'dependency': 'webserver',
                        'text': _("For optimal performance, use Apache as the webserver.")})
    if not depcheck.test_from_email():
        optimal.append({'dependency': 'from_email',
                        'text': _('The "from" address used to send registration emails is not specified. Also review the mail server settings.')})
    if not depcheck.test_contact_email():
        optimal.append({'dependency': 'contact_email',
                        'text': _("No contact address is specified. The contact form will allow users to contact the server administrators.")})

    if not depcheck.test_debug():
        optimal.append({'dependency': 'debug',
                        'text': _('Running in debug mode. Debug mode is only needed when developing Pootle. For optimal performance, disable debugging mode.')})

    if not depcheck.test_livetranslation():
        optimal.append({'dependency': 'livetranslation',
                       'text': _("Running in live translation mode. Live translation is useful as a tool to learn about Pootle and localization, but has high impact on performance.")})

    return optimal

def _format_numbers(dict):
    for k in dict.keys():
        dict[k] = locale.format("%d", dict[k], grouping=True)

def server_stats():
    result = cache.get("server_stats")
    if result is None:
        result = {}
        result['user_count'] = max(User.objects.filter(is_active=True).count()-2, 0)
        # 'default' and 'nobody' might be counted
        # FIXME: the special users should not be retuned with is_active
        result['submission_count'] = Submission.objects.count() + SuggestionStat.objects.count()
        result['pending_count'] = Suggestion.objects.count()
        cache.set("server_stats", result, 86400)
    _format_numbers(result)
    return result

@user_is_admin
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
        result['user_active_count'] = (PootleProfile.objects.exclude(submission=None) |\
                                       PootleProfile.objects.exclude(suggestion=None) |\
                                       PootleProfile.objects.exclude(suggester=None)).order_by().count()
        cache.set("server_stats_more", result, 86400)
    _format_numbers(result)
    stat_strings = {'store_count': _('Files'),
                    'project_count': _('Active projects'),
                    'language_count': _('Active languages'),
                    'string_count': _('Translated strings'),
                    'word_count': _('Translated words'),
                    'user_active_count': _('Active users')}
    response = []
    for k in result.keys():
        response.append((stat_strings[k], result[k]))
    response = simplejson.dumps(response)
    return HttpResponse(response, mimetype="application/json")

@user_is_admin
def view(request):
    template_vars = {
        'server_stats': server_stats(),
        'required': required_depcheck(),
        'optional': optional_depcheck(),
        'optimal': optimal_depcheck(),
        }
    return render_to_response("admin/dashboard.html", template_vars, context_instance=RequestContext(request))

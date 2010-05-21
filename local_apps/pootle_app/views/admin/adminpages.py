#!/usr/bin/python
# -*- coding: utf-8 -*-
#  Copyright 2006-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This file is somewhat based on the older Pootle/translatepage.py
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from django.utils.translation import ugettext as _

from pootle_app.views.admin.util import user_is_admin
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle import depcheck

from pootle_misc.siteconfig import load_site_config
from pootle_app.forms import GeneralSettingsForm


def required_depcheck():
    required = []

    status, version = depcheck.test_translate()
    if status:
        text = _('Translate Toolkit version %s installed.', version)
        state = 'good'
    else:
        text = _('Translate Toolkit version %(installed)s installed. Pootle requires version %(required)s.', {'installed': version, 'required': "1.7.0"})
        state = 'error'
    required.append({'dependency': 'translate', 'state': state, 'text': text })

    status = depcheck.test_sqlite()
    if status:
        text = _('SQLite is installed.')
        state = 'good'
    else:
        text = _('SQLite is missing. Pootle requires SQLite for translation statistics.')
        state = 'error'
    required.append({'dependency': 'sqlite', 'state': state, 'text': text })

    status, version = depcheck.test_django()
    if status:
        text = _('Django version %s is installed.', version)
        state = 'good'
    else:
        text = _('Django version %s is installed. Pootle only works with the 1.x series.')
        state = 'error'
    required.append({'dependency': 'django', 'state': state, 'text': text})

    return required

def optional_depcheck():
    optional = []

    if not depcheck.test_unzip():
        optional.append({'dependency': 'unzip',
                         'text': _('Can\'t find the unzip command. Uploading archives is faster if "unzip" is available.')})

    if not depcheck.test_iso_codes():
        optional.append({'dependency': 'iso-codes',
                           'text': _("Can't find the ISO codes package. Pootle uses ISO codes to translate language names.")})

    if not depcheck.test_lxml():
        optional.append({'dependency': 'lxml',
                            'text': _("Can't find lxml. Pootle uses lxml to parse XML based formats like XLIFF and Qt TS and to make sure HTML tags inserted in news items are safe and correct.")})
    if not depcheck.test_gaupol():
        optional.append({'dependency': 'gaupol',
                         'text': _("Can't find Gaupol. Pootle uses Gaupol's parser to support subtitles formats")})

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
                    if depcheck.test_cached_db_session():
                        text = _('For optimal performance, use django.contrib.sessions.backends.cached_db as the session engine.')
                    else:
                        text =  _('For optimal performance, use django.contrib.sessions.backends.cache as the session engine.')
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

    if not depcheck.test_debug():
        optimal.append({'dependency': 'debug',
                        'text': _('Running in debug mode. Debug mode is only needed when developing Pootle. For optimal performance, disable debugging mode.')})

    if not depcheck.test_livetranslation():
        optimal.append({'dependency': 'livetranslation',
                       'text': _("Running in live translation mode. Live translation is useful as a tool to learn about Pootle and localization, but has high impact on performance.")})

    return optimal


@user_is_admin
def view(request, path):
    siteconfig = load_site_config()
    if request.POST:
        setting_form = GeneralSettingsForm(siteconfig, data=request.POST)
        if setting_form.is_valid():
            setting_form.save()
            load_site_config()
    else:
        setting_form = GeneralSettingsForm(siteconfig)

    template = 'admin/admin_general_settings.html'
    template_vars = {
        'form': setting_form,
        'required': required_depcheck(),
        'optional': optional_depcheck(),
        'optimal': optimal_depcheck(),
        }
    return render_to_response(template, template_vars, context_instance=RequestContext(request))

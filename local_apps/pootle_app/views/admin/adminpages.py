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

from util import user_is_admin
from django.shortcuts import render_to_response
from django.template import RequestContext

from pootle import depcheck

from pootle_misc.siteconfig import load_site_config
from pootle_app.forms import GeneralSettingsForm


def requiered_depcheck():
    required = []
    
    status, version = depcheck.test_translate()
    if status:
        text = _('Translate Toolkit version %s installed', version)
        state = 'good'
    else:
        text = _('Found Translate Toolkit version %s installed, but Pootle requires version 1.4.1', version)
        state = 'error'
    required.append({'dependency': 'translate', 'state': state, 'text': text })

    status = depcheck.test_sqlite()
    if status:
        text = _('Found SQLite')
        state = 'good'
    else:
        text = _('SQLite missing, Pootle requires sqlite for calculating translation statistics')
        state = 'error'
    required.append({'dependency': 'sqlite', 'state': state, 'text': text })

    status, version = depcheck.test_django()
    if status:
        text = _('Django version %s installed', version)
        state = 'good'
    else:
        text = _('Found Django version %s installed, but Pootle only works with 1.x series')
        stats = 'error'
    required.append({'dependency': 'django', 'state': state, 'text': text})

    return required

def optional_depcheck():
    optional = []
    
    if not depcheck.test_unzip():
        optional.append({'dependency': 'unzip',
                         'text': _("Can't find the unzip command. Uploading archives is much quicker if unzip is available")})

    if not depcheck.test_iso_codes():
        optional.append({'dependency': 'iso-codes',
                           'text': _("Can't find Iso-codes package. Pootle uses iso-codes to translate language names")})

    if not depcheck.test_lxml():
        optional.append({'dependency': 'lxml',
                            'text': _("Can't find lxml. Pootle uses lxml to make sure html tags inserted in news items are safe and correct.")})

    if not depcheck.test_levenshtein():
        optional.append({'dependency': 'levenshtein',
                        'text': _("python-levenshtein missing. Updating from templates is much quicker with python-levenshtein")})

    if not depcheck.test_indexer():
        optional.append({'dependency': 'indexer',
                         'text': _("No text indexing engine found. Without a text indexing engine like Xapian or Lucene searching is too slow")})

    return optional


def optimal_depcheck():
    optimal = []

    if not depcheck.test_db():
        if depcheck.test_mysqldb():
            text = _("Using the default sqlite3 database engine. sqlite is only suitable for small installs with a small number of users. Pootle will perform better with the mysql database enginge")
        else:
            text = _("Using the default sqlite3 database engine. sqlite is only suitable for small installs with a small number of users. Pootle will perform better with the mysql database enginge but you need to install python-MySQLdb first.")
        optimal.append({'dependency': 'db', 'text': text})

    if depcheck.test_cache():
        if depcheck.test_memcache():
            if not depcheck.test_memcached():
                # memcached configured but connection failing
                optimal.append({'dependency': 'cache',
                                'text': _("Pootle configured to use memcached as caching backend but connection to memcached server is failing. caching is currently disabled")})
            else:
                if not depcheck.test_session():
                    from django import VERSION
                    if VERSION[1] == 0:
                        text =  _('For optimal performance use django.contrib.sessions.backends.cache as the session engine')
                    else:
                        text = _('For optimal performance use django.contrib.sessions.backends.cached_db as the session engine')
                    optimal.append({'dependency': 'session', 'text': text})
        else:
            optimal.append({'dependency': 'cache',
                            'text': _('Pootle configured to use memcached as caching backend but python support for memcache is not installed. caching is currently disabled')})
    else:
        optimal.append({'dependency': 'cache',
                        'text': _('For optimal performance use memcached as the caching backend')})

    if not depcheck.test_webserver():
        optimal.append({'dependency': 'webserver',
                        'text': _("For optimal performance use Apache as your webserver")})
        
    if not depcheck.test_debug():
        optimal.append({'dependency': 'debug',
                        'text': _('Running in debug mode, debug mode is only needed when developing Pootle. For optimal performance disable debugging mode')})

    if not depcheck.test_livetranslation():
        optimal.append({'dependency': 'livetranslation',
                       'text': _("Running in Live Translation mode, live translation is useful as a tool to learn about Pootle and localiztion but has high impact on performance")})

    return optimal


@user_is_admin
def view(request, path):
    siteconfig = load_site_config()
    if request.POST:
        post = request.POST.copy()
        setting_form = GeneralSettingsForm(siteconfig, data=post)
        if setting_form.is_valid():
            setting_form.save()
            load_site_config()
    else:
        setting_form = GeneralSettingsForm(siteconfig)

    template = 'admin/admin_general_settings.html'
    template_vars = {
        'form': setting_form,
        'required': requiered_depcheck(),
        'optional': optional_depcheck(),
        'optimal': optimal_depcheck(),
        }
    return render_to_response(template, template_vars, context_instance=RequestContext(request))

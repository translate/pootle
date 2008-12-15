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

import os
from os import path

from django.utils.cache import patch_vary_headers
from django.utils.translation import trans_real
from django.conf import settings

from translate.lang import data as langdata

from Pootle import settings as pootle_settings
from Pootle import pan_app
from Pootle.pootle_app import models

po_tree = pan_app.get_po_tree()
pootle_project_path = os.path.join(os.path.dirname(pootle_settings.__file__), 'po', 'pootle')

def get_lang(code):
    return po_tree.getproject(code, 'pootle')

def check_for_language(code):
    return 'pootle' in po_tree.projects and code in po_tree.languages

def get_lang_from_cookie(request):
    from django.conf import settings

    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
    if lang_code and lang_code in supported and check_for_language(lang_code):
        return get_lang(lang_code)
    return None

def get_lang_from_http_header(request):
    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for accept_lang, unused in trans_real.parse_accept_lang_header(accept):
        if accept_lang == '*':
            return get_lang('en')
        if check_for_language(accept_lang):
            return get_lang(accept_lang)
    return None

def get_lang_from_prefs(request):
    # If the user is logged in
    if not request.user.is_anonymous:
        profile = models.get_profile(request.user)
        # and if the user's ui lang is set, and the ui lang exists
        if profile.ui_lang is not None and check_for_language(profile.ui_lang.code):
            # return that
            return get_lang(profile.ui_lang.code)
    return None

def get_language_from_request(request):
    for lang_getter in (get_lang_from_cookie,
                     get_lang_from_prefs,
                     get_lang_from_http_header):
        lang = lang_getter(request)
        if lang is not None:
            return lang
    return get_lang('en')

# Taken from jToolkit
def make_localize(translation):
    def localize(message, *variables):
        if variables:
            try:
                return translation.ugettext(message) % variables
            except:
                return message % variables
        else:
            return translation.ugettext(message)

    return localize

# Taken from jToolkit
def make_nlocalize(translation):
    def nlocalize(singular, plural, n, *variables):
        """returns the localized form of a plural message, falls back to
        original if failure with variables"""
        if variables:
            try:
                return translation.ungettext(singular, plural, n) % variables
            except:
                if n != 1:
                    return plural % variables
                else:
                    return singular % variables
        else:
            return translation.ungettext(singular, plural, n)

    return nlocalize

# Taken from jToolkit
def make_tr_lang(translation):
    def tr_lang(language_name):
        return langdata.tr_lang(translation.languagecode)(language_name)

    return tr_lang

class LocaleMiddleware(object):
    """
    This is a very simple middleware that parses a request
    and decides what translation object to install in the current
    thread context. This allows pages to be dynamically
    translated to the language the user desires (if the language
    is available, of course).
    """

    def process_request(self, request):
        request.ui_lang_project = get_language_from_request(request)
        request.localize        = make_localize(request.ui_lang_project)
        request.nlocalize       = make_nlocalize(request.ui_lang_project)
        request.tr_lang         = make_tr_lang(request.ui_lang_project)

    def process_response(self, request, response):
        patch_vary_headers(response, ('Accept-Language',))
        if 'Content-Language' not in response:
            response['Content-Language'] = request.ui_lang_project.languagecode
        return response

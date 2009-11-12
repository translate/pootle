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

"""overrides and support functions for enabling Live Translation and
arbitrary locale support"""

import locale

from django.conf import settings
from django.utils.translation import trans_real

from translate.lang import data

def supported_langs():
    if settings.LIVE_TRANSLATION:
        from django.db import models
        Language = models.get_model('pootle_app', 'Language')
        return ((language.code, language.fullname) for language in Language.objects.all())
    else:
        return settings.LANGUAGES


def lang_choices():
    choices = []
    for code, name in supported_langs():
        tr_name = data.tr_lang(code)(name)
        if tr_name != name:
            # We have to use the LRO (left-to-right override) to ensure that 
            # brackets in the English part of the name is rendered correctly
            # in an RTL layout like Arabic. We can't use markup because this 
            # is used inside an option tag.
            name = u"%s | \u202d%s" % (tr_name, name)
        choices.append((code, name))
    choices.sort(cmp=locale.strcoll, key=lambda choice: unicode(choice[1]))
    return choices


def get_lang_from_cookie(request, supported):
    """See if the user's browser sent a cookie with a her preferred
    language."""
    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
    if lang_code and lang_code in supported:
        return lang_code
    else:
        return None

def get_lang_from_prefs(request, supported):
    """If the current user is logged in, get her profile model object
    and check whether she has set her preferred interface language."""
    # If the user is logged in
    if request.user.is_authenticated():
        profile = request.user.get_profile()
        # and if the user's ui lang is set, and the ui lang exists
        if profile.ui_lang and profile.ui_lang in supported:
            return profile.ui_lang
    return None


def get_lang_from_http_header(request, supported):
    """If the user's browser sends a list of preferred languages in the
    HTTP_ACCEPT_LANGUAGE header, parse it into a list. Then walk through
    the list, and for each entry, we check whether we have a matching
    pootle translation project. If so, we return it.

    If nothing is found, return None."""
    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for accept_lang, unused in trans_real.parse_accept_lang_header(accept):
        if accept_lang == '*':
            return None
        #normalized = data.normalize_code(accept_lang)
        normalized = data.simplify_to_common(accept_lang)
        if normalized in ['en-us', 'en']:
            return None
        if normalized in supported:
            return normalized
    return None


def get_language_from_request(request):
    """Try to get the user's preferred language by first checking the
    cookie, then the user's preferences (stored in the PootleProfile
    model) and finally by checking the HTTP language headers.

    If all fails, try fall back to default language."""
    supported = dict(supported_langs())
    for lang_getter in (get_lang_from_cookie,
                        get_lang_from_prefs,
                        get_lang_from_http_header):
        lang = lang_getter(request, supported)
        if lang is not None:
            return lang

    return settings.LANGUAGE_CODE

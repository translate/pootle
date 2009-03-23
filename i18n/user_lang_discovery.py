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

"""These functions are concerned with discovering the language which should
be used to display Pootle's UI to a user."""

from django.utils.translation import trans_real
from django.conf import settings
from django.core.exceptions import ObjectDoesNotExist

from pootle_app.models import Language
from pootle_app.models.profile import get_profile
from pootle_app.models.translation_project import TranslationProject
from Pootle.i18n import gettext

from translate.lang import data

from string import upper

def get_lang_from_cookie(request):
    """See if the user's browser sent a cookie with her preferred language. Return
    a Pootle project object if so and if the we have a pootle translation project
    for the language.

    Otherwise, return None."""
    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, None)
    # FIXME: removed checking if language is supported
    if lang_code and gettext.check_for_language(lang_code):
        return gettext.get_lang(Language.objects.get(code=lang_code))
    return None

def get_lang_obj(code):
    """Tries to get a Language object based on a language code from an HTTP header.

       Since the header can be in the form 'af-za' or 'af', we first try with
       the 'lang_COUNTRY' form and otherwise fallback to 'lang'. Also,
       language codes are normalized to the form 'af_ZA', because this is how
       Pootle stores language codes."""
    code_parts = code.split('-')
    if len(code_parts) > 1:
        code2 = "%(lang)s_%(country)s" % {'lang': code_parts[0],
                                          'country': upper(code_parts[1])}
        # First try with the lang_COUNTRY code, and if it fails
        # then try with the language code only
        try:
            return Language.objects.get(code=code2)
        except ObjectDoesNotExist:
            pass
    try:
        return Language.objects.get(code=code_parts[0])
    except ObjectDoesNotExist:
        return None

def get_lang_from_http_header(request):
    """If the user's browser sends a list of preferred languages in the
    HTTP_ACCEPT_LANGUAGE header, parse it into a list. Then walk through
    the list, and for each entry, we check whether we have a matching
    pootle translation project. If so, we return it.

    If nothing is found, return None."""
    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for accept_lang, unused in trans_real.parse_accept_lang_header(accept):
        if accept_lang == '*' or data.normalize_code(accept_lang) in ['en-us', 'en']:
            return gettext.get_default_translation()
        try:
            lang_obj = get_lang_obj(accept_lang)
            return gettext.get_lang(lang_obj)
        except TranslationProject.DoesNotExist:
            pass
    return None

def get_lang_from_prefs(request):
    """If the current user is logged in, get her profile model object and check
    whether she has set her preferred interface language.

    If she has, and we have a Pootle translation project, return the associate
    Pootle translation object.

    Otherwise, return None."""
    # If the user is logged in
    if request.user.is_authenticated():
        profile = get_profile(request.user)
        # and if the user's ui lang is set, and the ui lang exists
        if profile.ui_lang is not None and gettext.check_for_language(profile.ui_lang.code):
            # return that
            return gettext.get_lang(profile.ui_lang)
    return None

def get_language_from_request(request):
    """Try to get the Pootle project object for the user's preferred language
    by first checking the cookie, then the user's preferences (stored in the PootleProfile
    model) and finally by checking the HTTP language headers.

    If all fails, try to fall back to English."""
    for lang_getter in (get_lang_from_prefs,
                        get_lang_from_cookie,
                        get_lang_from_http_header):
        lang = lang_getter(request)
        if lang is not None:
            return lang
    return gettext.get_default_translation()


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

from Pootle.pootle_app import models
from Pootle.i18n import gettext

def get_lang_from_cookie(request):
    """See if the user's browser sent a cookie with her preferred language. Return
    a Pootle project object if so and if the we have a pootle translation project
    for the language.

    Otherwise, return None."""
    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME, None)
    if lang_code and gettext.check_for_language(lang_code): # FIXME: removed checking if language is supported
        return gettext.get_lang(lang_code)
    return None

def get_lang_from_http_header(request):
    """If the user's browser sends a list of preferred languages in the
    HTTP_ACCEPT_LANGUAGE header, parse it into a list. Then walk through
    the list, and for each entry, we check whether we have a matching
    pootle translation project. If so, we return it.

    If nothing is found, return None."""
    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for accept_lang, unused in trans_real.parse_accept_lang_header(accept):
        if accept_lang == '*':
            return gettext.get_lang('en')
        # TODO: This will fail for language codes such as af-ZA.
        #       We should split such codes into two components
        #       ('af' and 'ZA') and also check whether we have
        #       a project matching the first component ('af').
        if gettext.check_for_language(accept_lang):
            return gettext.get_lang(accept_lang)
    return None

def get_lang_from_prefs(request):
    """If the current user is logged in, get her profile model object and check
    whether she has set her preferred interface language.

    If she has, and we have a Pootle translation project, return the associate
    Pootle translation object.

    Otherwise, return None."""
    # If the user is logged in
    if request.user.is_authenticated():
        profile = models.get_profile(request.user)
        # and if the user's ui lang is set, and the ui lang exists
        if profile.ui_lang is not None and gettext.check_for_language(profile.ui_lang.code):
            # return that
            return gettext.get_lang(profile.ui_lang.code)
    return None

def get_language_from_request(request):
    """Try to get the Pootle project object for the user's preferred language
    by first checking the cookie, then the user's preferences (stored in the PootleProfile
    model) and finally by checking the HTTP language headers.

    If all fails, try to fall back to English."""
    for lang_getter in (get_lang_from_cookie,
                        get_lang_from_prefs,
                        get_lang_from_http_header):
        lang = lang_getter(request)
        if lang is not None:
            return lang
    return gettext.get_lang('en')

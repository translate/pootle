# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Overrides and support functions for arbitrary locale support."""

import os

from translate.lang import data

from django.utils import translation
from django.utils.translation import LANGUAGE_SESSION_KEY, trans_real

from pootle.i18n import gettext


def find_languages(locale_path):
    """Generate supported languages list from the :param:`locale_path`
    directory.
    """
    dirs = os.listdir(locale_path)
    langs = []
    for lang in dirs:
        if (data.langcode_re.match(lang) and
            os.path.isdir(os.path.join(locale_path, lang))):
            langs.append((trans_real.to_language(lang),
                          data.languages.get(lang, (lang,))[0]))
    return langs


def supported_langs():
    """Returns a list of supported locales."""
    from django.conf import settings
    return settings.LANGUAGES


def get_language_supported(lang_code, supported):
    normalized = data.normalize_code(data.simplify_to_common(lang_code))
    if normalized in supported:
        return normalized

    # FIXME: horribly slow way of dealing with languages with @ in them
    for lang in supported.keys():
        if normalized == data.normalize_code(lang):
            return lang

    return None


def get_lang_from_session(request, supported):
    if not hasattr(request, 'session'):
        return None
    lang_code = request.session.get(LANGUAGE_SESSION_KEY, None)
    if not lang_code:
        return None
    return get_language_supported(lang_code, supported)


def get_lang_from_cookie(request, supported):
    """See if the user's browser sent a cookie with a preferred language."""
    from django.conf import settings
    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)
    if not lang_code:
        return None
    return get_language_supported(lang_code, supported)


def get_lang_from_http_header(request, supported):
    """If the user's browser sends a list of preferred languages in the
    HTTP_ACCEPT_LANGUAGE header, parse it into a list. Then walk through
    the list, and for each entry, we check whether we have a matching
    pootle translation project. If so, we return it.

    If nothing is found, return None.
    """
    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for accept_lang, __ in trans_real.parse_accept_lang_header(accept):
        if accept_lang == '*':
            return None
        supported_lang = get_language_supported(accept_lang, supported)
        if supported_lang:
            return supported_lang
    return None


def get_language_from_request(request, check_path=False):
    """Try to get the user's preferred language by first checking the
    cookie and then by checking the HTTP language headers.

    If all fails, try fall back to default language.
    """
    supported = dict(supported_langs())
    for lang_getter in (get_lang_from_session,
                        get_lang_from_cookie,
                        get_lang_from_http_header):
        lang = lang_getter(request, supported)
        if lang is not None:
            return lang
    from django.conf import settings
    if settings.LANGUAGE_CODE in supported:
        return settings.LANGUAGE_CODE
    return 'en-us'


def get_language_bidi():
    """Override for Django's get_language_bidi that's aware of more RTL
    languages.
    """
    return gettext.language_dir(translation.get_language()) == 'rtl'


def hijack_translation():
    """Sabotage Django's fascist linguistical regime."""
    # Override functions that check if language is known to Django
    translation.check_for_language = lambda lang_code: True
    trans_real.check_for_language = lambda lang_code: True
    translation.get_language_from_request = get_language_from_request

    # Override django's inadequate bidi detection
    translation.get_language_bidi = get_language_bidi

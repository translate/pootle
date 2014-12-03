#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
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

"""Overrides and support functions for arbitrary locale support."""

import locale
import os

from django.utils import translation
from django.utils.functional import lazy
from django.utils.translation import trans_real

from translate.lang import data

from pootle.i18n import bidi, gettext


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


def lang_choices():
    """Generate locale choices for drop down lists in forms."""
    choices = []
    for code, name in supported_langs():
        name = data.tr_lang(translation.to_locale('en'))(name)
        tr_name = data.tr_lang(translation.to_locale(code))(name)
        # We have to use the bidi.insert_embeding() to ensure that brackets
        # in the English part of the name is rendered correctly in an RTL
        # layout like Arabic. We can't use markup because this is used
        # inside an option tag.
        if tr_name != name:
            name = u"%s | %s" % (bidi.insert_embeding(tr_name),
                                 bidi.insert_embeding(name))
        else:
            name = bidi.insert_embeding(name)
        choices.append((code, name))

    choices.sort(cmp=locale.strcoll, key=lambda choice: unicode(choice[1]))
    return choices


def get_lang_from_session(request, supported):
    if hasattr(request, 'session'):
        lang_code = request.session.get('django_language', None)
        if lang_code and lang_code in supported:
            return lang_code

    return None


def get_lang_from_cookie(request, supported):
    """See if the user's browser sent a cookie with a preferred language."""
    from django.conf import settings
    lang_code = request.COOKIES.get(settings.LANGUAGE_COOKIE_NAME)

    if lang_code and lang_code in supported:
        return lang_code
    else:
        return None


def get_lang_from_http_header(request, supported):
    """If the user's browser sends a list of preferred languages in the
    HTTP_ACCEPT_LANGUAGE header, parse it into a list. Then walk through
    the list, and for each entry, we check whether we have a matching
    pootle translation project. If so, we return it.

    If nothing is found, return None.
    """
    accept = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
    for accept_lang, unused in trans_real.parse_accept_lang_header(accept):
        if accept_lang == '*':
            return None

        normalized = data.normalize_code(data.simplify_to_common(accept_lang))
        if normalized in ['en-us', 'en']:
            return None
        if normalized in supported:
            return normalized

        #FIXME: horribly slow way of dealing with languages with @ in them
        for lang in supported.keys():
            if normalized == data.normalize_code(lang):
                return lang
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
    return settings.LANGUAGE_CODE


def override_gettext(real_translation):
    """Replace Django's translation functions with safe versions."""
    translation.gettext = real_translation.gettext
    translation.ugettext = real_translation.ugettext
    translation.ngettext = real_translation.ngettext
    translation.ungettext = real_translation.ungettext
    translation.gettext_lazy = lazy(real_translation.gettext, str)
    translation.ugettext_lazy = lazy(real_translation.ugettext, unicode)
    translation.ngettext_lazy = lazy(real_translation.ngettext, str)
    translation.ungettext_lazy = lazy(real_translation.ungettext, unicode)


def get_language_bidi():
    """Override for Django's get_language_bidi that's aware of more
    RTL languages."""
    return gettext.language_dir(translation.get_language()) == 'rtl'


def hijack_translation():
    """Sabotage Django's fascist linguistical regime."""
    # Override functions that check if language is known to Django
    translation.check_for_language = lambda lang_code: True
    trans_real.check_for_language = lambda lang_code: True
    translation.get_language_from_request = get_language_from_request

    # Override django's inadequate bidi detection
    translation.get_language_bidi = get_language_bidi

    # We hijack gettext functions to install the safe variable formatting
    # override
    override_gettext(gettext)

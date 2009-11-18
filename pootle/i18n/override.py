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
import os

from django.utils import translation
from django.utils.translation import trans_real
from django.utils.functional import lazy

from pootle.i18n import gettext
from pootle.i18n import  gettext_live

from translate.lang import data

def find_languages(locale_path):
    """generates supported languages list from mo directory"""
    dirs = os.listdir(locale_path)
    langs = []
    for lang in dirs:
        if data.langcode_re.match(lang) and os.path.isdir(os.path.join(locale_path, lang)):
            langs.append((data.normalize_code(lang), data.languages.get(lang, (lang,))[0]))
    return langs


def supported_langs():
    """returns list of locales supported adapting to live translation
    state"""
    from django.conf import settings
    if settings.LIVE_TRANSLATION:
        try:
            # hackish: we import PootleProfile to force a failure when
            # first initializing the PootleProfile model, this way
            # Language is never created before PootleProfile and all
            # ManyToMany relations work fine
            from pootle_app.models import PootleProfile, Language
            return [(data.normalize_code(language.code), language.fullname) for language in Language.objects.exclude(code='template')]
        except Exception:
            pass
    return settings.LANGUAGES


def lang_choices():
    """generated locale choices for drop down lists in forms"""
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
    from django.conf import settings
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
        normalized = data.normalize_code(data.simplify_to_common(accept_lang, supported))
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
    from django.conf import settings
    return settings.LANGUAGE_CODE


def translation_dummy(language):
    """return dumy translation object to please django's l10n while
    Live Translation is enabled"""

    t = trans_real._translations.get(language, None)
    if t is not None:
        return t

    dummytrans = trans_real.DjangoTranslation()
    dummytrans.set_language(language)
    #FIXME: the need for the _catalog attribute means we
    # are not hijacking gettext early enough
    dummytrans._catalog = {}
    dummytrans.plural = lambda x: x
    trans_real._translations[language] = dummytrans
    return dummytrans

def override_gettext(real_translation):
    """replace django's translation functions with safe versions"""
    translation.gettext = real_translation.gettext
    translation.ugettext = real_translation.ugettext
    translation.ngettext = real_translation.ngettext
    translation.ungettext = real_translation.ungettext
    translation.gettext_lazy = lazy(real_translation.gettext, str)
    translation.ugettext_lazy = lazy(real_translation.ugettext, unicode)
    translation.ngettext_lazy = lazy(real_translation.ngettext, str)
    translation.ungettext_lazy = lazy(real_translation.ungettext, unicode)

def get_language_bidi():
    """override for django's get_language_bidi that's aware of more
    RTL languages"""
    return gettext.language_dir(translation.get_language()) == 'rtl'

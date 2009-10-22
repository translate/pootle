#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from translate.lang import data as langdata

from django.utils import translation
from django.utils.functional import lazy

# override gettext function that handle variable errors more
# gracefully.
#
# needed to avoid tracebacks on translation errors with live
# translation

def _format_gettext(f):
    """decorator for failsafe variable formatting in gettext functions"""
    def format_gettext(message, vars=None):
        translated = f(message)
        if vars is not None:
            try:
                return translated % vars
            except:
                pass
        return translated
    return format_gettext


def _format_ngettext(f):
    """decorator for failsafe variable formatting in ngettext
    functions"""
    def format_ngettext(singular, plural, number, vars=None):
        translated = f(singular, plural, number)
        if vars is not None:
            try:
                return translated % vars
            except:
                pass
        return translated
    return format_ngettext


def override_gettext(real_translation):
    """replace django's translation functions with decorated versions
    of translation functions"""
    translation.gettext = _format_gettext(real_translation.gettext)
    translation.ngettext = _format_ngettext(real_translation.ngettext)
    translation.ugettext = _format_gettext(real_translation.ugettext)
    translation.ungettext = _format_ngettext(real_translation.ungettext)

    translation.gettext_lazy = lazy(translation.gettext, str)
    translation.ngettext_lazy = lazy(translation.ngettext, str)
    translation.ugettext_lazy = lazy(translation.ugettext, unicode)
    translation.ungettext_lazy = lazy(translation.ungettext, unicode)
    


def tr_lang(request, language_name):
    """translate language name"""
    return langdata.tr_lang(request.LANGUAGE_CODE)(language_name)

def get_language_bidi():
    return language_dir(translation.get_language()) == 'rtl'

def language_dir(language_code):
    """Returns whether the language is right to left"""
    shortcode = language_code[:3]
    if not shortcode.isalpha():
        shortcode = language_code[:2]
    if shortcode in ["ar", "arc", "dv", "fa", "he", "ks", "ps", "ur", "yi", "nqo"]:
        return "rtl"
    return "ltr"


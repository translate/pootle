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

# override gettext function that handle variable errors more
# gracefully.
#
# needed to avoid tracebacks on translation errors with live
# translation
def _format_translation(message, vars=None):
    if vars is not None:
        try:
            return message % vars
        except:
            pass
    return message

def ugettext(message, vars=None):
    return _format_translation(translation.real_ugettext(message), vars)

def gettext(message, vars=None):
    return _format_translation(translation.real_gettext(message), vars)

def ungettext(singular, plural, number, vars=None):
    return _format_translation(translation.real_ungettext(singular, plural, number), vars)

def ngettext(singular, plural, number, vars=None):
    return _format_translation(translation.real_ngettext(singular, plural, number), vars)

def tr_lang(language_name):
    """translate language name"""
    language_code = translation.to_locale(translation.get_language())
    return langdata.tr_lang(language_code)(language_name)

def language_dir(language_code):
    """Returns whether the language is right to left"""
    shortcode = language_code[:3]
    if not shortcode.isalpha():
        shortcode = language_code[:2]
    if shortcode in ["ar", "arc", "dv", "fa", "he", "ks", "ps", "ur", "yi", "nqo"]:
        return "rtl"
    return "ltr"

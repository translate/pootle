#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
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

from django.utils import translation
from django.utils.translation import _trans

from translate.lang import data as langdata


def _format_translation(message, vars=None):
    """Overrides the gettext function, handling variable errors more
    gracefully.

    This is needed to avoid tracebacks on translation errors with live
    translation.
    """
    if vars is not None:
        try:
            return message % vars
        except:
            pass

    return message


def ugettext(message, vars=None):
    return _format_translation(_trans.ugettext(message), vars)


def gettext(message, vars=None):
    return _format_translation(_trans.gettext(message), vars)


def ungettext(singular, plural, number, vars=None):
    return _format_translation(_trans.ungettext(singular, plural, number),
                               vars)


def ngettext(singular, plural, number, vars=None):
    return _format_translation(_trans.ngettext(singular, plural, number), vars)


def tr_lang(language_name):
    """Translates language names."""
    language_code = translation.to_locale(translation.get_language())

    return langdata.tr_lang(language_code)(language_name)


def language_dir(language_code):
    """Returns whether the language is right to left"""
    RTL_LANGS = [
        "ar", "arc", "dv", "fa", "he", "ks", "ps", "ug", "ur", "yi", "nqo"
    ]
    shortcode = language_code[:3]

    if not shortcode.isalpha():
        shortcode = language_code[:2]

    if shortcode in RTL_LANGS:
        return "rtl"

    return "ltr"

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from translate.lang import data as langdata

from django.conf import settings
from django.utils import translation
from django.utils.translation import _trans


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
    language_code = translation.get_language()
    if language_code is None:
        language_code = settings.LANGUAGE_CODE
    language_code = translation.to_locale(language_code)

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

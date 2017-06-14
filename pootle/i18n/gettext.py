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
from django.utils.functional import lazy
from django.utils.translation import _trans


def _format_translation(message, variables=None):
    """Overrides the gettext function, handling variable errors more
    gracefully.

    This is needed to avoid tracebacks on translation errors with live
    translation.
    """
    if variables is not None:
        try:
            return message % variables
        except:
            pass

    return message


def ugettext(message, variables=None):
    return _format_translation(_trans.ugettext(message), variables)


def gettext(message, variables=None):
    return _format_translation(_trans.gettext(message), variables)


def ungettext(singular, plural, number, variables=None):
    return _format_translation(_trans.ungettext(singular, plural, number),
                               variables)


def ngettext(singular, plural, number, variables=None):
    return _format_translation(_trans.ngettext(singular, plural, number), variables)


gettext_lazy = lazy(gettext, str)
ugettext_lazy = lazy(ugettext, unicode)
ngettext_lazy = lazy(ngettext, str)
ungettext_lazy = lazy(ungettext, unicode)


def tr_lang(language_name):
    """Translates language names."""
    return langdata.tr_lang(
        translation.to_locale(
            translation.get_language()
            or settings.LANGUAGE_CODE))(language_name)


def language_dir(language_code):
    """Returns whether the language is right to left"""
    RTL_LANGS = [
        # Helpful list of RTL codes:
        # https://en.wikipedia.org/wiki/Right-to-left#RTL_Wikipedia_languages
        'ar', 'arc', 'bcc', 'bqi', 'ckb', 'dv', 'fa', 'glk', 'he', 'ks', 'lrc',
        'mzn', 'pnb', 'ps', 'sd', 'ug', 'ur', 'yi', 'nqo',
        # and
        # https://github.com/i18next/i18next/blob/ee3afd8e5d958e8d703a208194e59fa5228165fd/src/i18next.js#L257-L262
        'shu', 'sqr', 'ssh', 'xaa', 'yhd', 'yud', 'aao', 'abh', 'abv', 'acm',
        'acq', 'acw', 'acx', 'acy', 'adf', 'ads', 'aeb', 'aec', 'afb', 'ajp',
        'apc', 'apd', 'arb', 'arq', 'ars', 'ary', 'arz', 'auz', 'avl', 'ayh',
        'ayl', 'ayn', 'ayp', 'bbz', 'pga', 'iw', 'pbt', 'pbu', 'pst', 'prp',
        'prd', 'ydd', 'yds', 'yih', 'ji', 'hbo', 'men', 'xmn', 'jpr', 'peo',
        'pes', 'prs', 'sam',
    ]
    shortcode = language_code[:3]

    if not shortcode.isalpha():
        shortcode = language_code[:2]

    if shortcode in RTL_LANGS:
        return "rtl"

    return "ltr"

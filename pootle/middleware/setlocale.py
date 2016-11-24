# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import locale
import logging
import os

from django.conf import settings
from django.utils import translation
from django.utils.deprecation import MiddlewareMixin


class SetLocale(MiddlewareMixin):
    """Sets python locale for each request."""

    def process_request(self, request):
        # Under Windows, locale names are different, setlocale() with regular
        # locale names will fail and locale.setlocale(locale.LC_ALL, '') will
        # produce side effect seems like the safest option is just not set any
        # locale at all
        if os.name == 'nt':
            return

        # FIXME: some languages like arabic don't have a language only locale
        # for no good reason. we need a function to pick default locale for
        # these
        lang = translation.to_locale(translation.get_language())
        try:
            if lang == 'tr' or lang.startswith('tr_'):
                raise ValueError("Turkish locale broken due to changed "
                                 "meaning of lower()")
            locale.setlocale(locale.LC_ALL, (lang, 'UTF-8'))
        except:
            logging.debug('Failed to set locale to %s; using Pootle default',
                          lang)
            set_pootle_locale_from_settings()

    def process_response(self, request, response):
        set_pootle_locale_from_settings()
        return response

    def process_exception(self, request, exception):
        set_pootle_locale_from_settings()


def set_pootle_locale_from_settings():
    """Try to set Pootle locale based on the language specified in settings."""

    # See above for the reasoning why we need to skip setting locale under
    # Windows
    if os.name == 'nt':
        return

    lang = translation.to_locale(settings.LANGUAGE_CODE)
    try:
        if lang == 'tr' or lang.startswith('tr_'):
            raise ValueError("Turkish locale broken due to changed meaning of "
                             "lower()")
        locale.setlocale(locale.LC_ALL, (lang, 'UTF-8'))
    except:
        logging.debug('Failed to set locale to Pootle default (%s); loading '
                      'system default', lang)
        locale.setlocale(locale.LC_ALL, '')

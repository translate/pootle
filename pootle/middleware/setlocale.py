#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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

import locale
import logging
import os

from django.conf import settings
from django.utils import translation


class SetLocale(object):
    """Sets python locale for each request."""

    def process_request(self, request):
        # Under Windows, locale names are different, setlocale()
        # with regular locale names will fail and
        # locale.setlocale(locale.LC_ALL, '') will produce side effect
        # seems like the safest option is just not set any locale at all
        if os.name == 'nt':
            return

        #FIXME: some languages like arabic don't have a language only
        # locale for no good reason. we need a function to pick default
        # locale for these
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

    # See above for the reasoning why we need to skip
    # setting locale under Windows
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

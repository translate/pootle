#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2010 Zuza Software Foundation
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

from django.utils import translation
from django.conf import settings

class SetLocale(object):
    """sets python locale for each request"""
    def process_request(self, request):
        #FIXME: some languages like arabic don't have a language only
        # locale for no good reason. we need a function to pick default
        # locale for these
        lang = translation.to_locale(translation.get_language())
        try:
            locale.setlocale(locale.LC_ALL, (lang, 'UTF-8'))
        except:
            logging.debug('failed to set locale to %s; using Pootle default', lang)
            lang = translation.to_locale(settings.LANGUAGE_CODE)
            try:
                locale.setlocale(locale.LC_ALL, (lang, 'UTF-8'))
            except:
                logging.debug('failed to set locale to pootle default (%s); loading system default', lang)
                locale.setlocale(locale.LC_ALL, '')

    def process_response(self, request, response):
        lang = translation.to_locale(settings.LANGUAGE_CODE)
        try:
            locale.setlocale(locale.LC_ALL, (lang, 'UTF-8'))
        except:
            logging.debug('failed to set locale to pootle default (%s); loading system default', lang)
            locale.setlocale(locale.LC_ALL, '')
        return response

    def process_exception(self, request, exception):
        lang = translation.to_locale(settings.LANGUAGE_CODE)
        try:
            locale.setlocale(locale.LC_ALL, (lang, 'UTF-8'))
        except:
            logging.debug('failed to set locale to pootle default (%s); loading system default', lang)
            locale.setlocale(locale.LC_ALL, '')

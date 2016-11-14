# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import locale as system_locale
import os
from datetime import datetime

from babel.dates import format_timedelta

from django.utils import translation


class LocalDate(object):

    def __init__(self):
        if not self.locale_code and not os.name == "nt":
            self.set_locale()

    @property
    def default_locale(self):
        return translation.to_locale(translation.get_language())

    def set_locale(self):
        system_locale.setlocale(
            system_locale.LC_ALL,
            (self.default_locale, 'UTF-8'))

    @property
    def locale_code(self):
        return system_locale.getlocale()[0]

    def format_timesince(self, timestamp, locale=None):
        return format_timedelta(
            datetime.now()
            - datetime.fromtimestamp(
                timestamp),
            locale=(
                locale
                or self.locale_code
                or self.default_locale))


localdate = LocalDate()


def timesince(timestamp, locale=None):
    return localdate.format_timesince(timestamp, locale=locale)

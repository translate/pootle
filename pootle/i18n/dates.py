# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import datetime

from django.conf import settings

from .formatter import get_locale_formats


def timesince(timestamp, locale=None):
    timedelta = datetime.now() - datetime.fromtimestamp(timestamp)
    formatted = get_locale_formats(locale).timedelta(timedelta, format='long')
    if formatted:
        return formatted
    return get_locale_formats(
        settings.LANGUAGE_CODE).timedelta(timedelta, format='long')

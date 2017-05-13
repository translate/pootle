# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest
import time
from datetime import datetime

from babel.dates import format_timedelta

from pootle.i18n.dates import timesince
from pootle.i18n.formatter import get_locale_formats


def test_local_date_timesince(settings):
    timestamp = time.time() - 1000000
    timedelta = datetime.now() - datetime.fromtimestamp(timestamp)
    language = str(get_locale_formats().locale)
    assert timesince(timestamp) == format_timedelta(timedelta, locale=language)
    assert (
        timesince(timestamp, locale="ff")
        == timesince(timestamp, locale=settings.LANGUAGE_CODE))


@pytest.mark.parametrize('language,fallback', [
    # Normal
    ('af', 'af'),
    ('en-za', 'en-za'),
    ('en-us', 'en-us'),
    # Code from ISO 639 reserved range (cannot be used to represent a language)
    # so we know for sure it has to fall back.
    ('qbb', 'en-us'),
])
def test_local_date_timesince_wrong_locale(language, fallback):
    timestamp = time.time() - 1000000
    timedelta = datetime.now() - datetime.fromtimestamp(timestamp)
    fallback_format = get_locale_formats(fallback)
    fallback_timedelta = fallback_format.timedelta(timedelta, format='long')
    assert timesince(timestamp, locale=language) == fallback_timedelta

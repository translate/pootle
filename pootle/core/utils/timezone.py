# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import datetime

from django.conf import settings
from django.utils import timezone


# Timezone aware minimum for datetime (if appropriate) (bug 2567)
datetime_min = datetime.datetime.min
if settings.USE_TZ:
    datetime_min = timezone.make_aware(datetime_min, timezone.utc)


def localdate(dt=None):
    dt = dt or timezone.now()
    return timezone.localtime(dt).date()


def make_aware(value, tz=None):
    """Makes a `datetime` timezone-aware.

    :param value: `datetime` object to make timezone-aware.
    :param tz: `tzinfo` object with the timezone information the given value
        needs to be converted to. By default, site's own default timezone will
        be used.
    """
    if getattr(settings, 'USE_TZ', False) and timezone.is_naive(value):
        use_tz = tz if tz is not None else timezone.get_default_timezone()
        value = timezone.make_aware(value, timezone=use_tz)

    return value


def make_naive(value, tz=None):
    """Makes a `datetime` naive, i.e. not aware of timezones.

    :param value: `datetime` object to make timezone-aware.
    :param tz: `tzinfo` object with the timezone information the given value
        needs to be converted to. By default, site's own default timezone will
        be used.
    """
    if getattr(settings, 'USE_TZ', False) and timezone.is_aware(value):
        use_tz = tz if tz is not None else timezone.get_default_timezone()
        value = timezone.make_naive(value, timezone=use_tz)

    return value


def aware_datetime(*args, **kwargs):
    """Creates a `datetime` object and makes it timezone-aware.

    :param args: arguments passed to `datetime` constructor.
    :param tz: timezone in which the `datetime` should be constructed. Note that
        this bypasses passing `tzinfo` to the `datetime` constructor, as it is
        known not to play well with DST (unless only UTC is used).
    """
    tz = kwargs.pop('tz', None)
    return make_aware(datetime.datetime(*args, **kwargs), tz=tz)

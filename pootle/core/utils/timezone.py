#!/usr/bin/env python
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


def make_aware(value):
    if getattr(settings, 'USE_TZ', False) and timezone.is_naive(value):
        tz = timezone.get_default_timezone()
        value = timezone.make_aware(value, tz)

    return value


def make_naive(value):
    if getattr(settings, 'USE_TZ', False) and timezone.is_aware(value):
        tz = timezone.get_default_timezone()
        value = timezone.make_naive(value, tz)

    return value


def aware_datetime(*args, **kwargs):
    return make_aware(datetime.datetime(*args, **kwargs))

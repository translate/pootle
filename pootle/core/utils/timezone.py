#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2015 Evernote Corporation
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

import datetime

from django.conf import settings
from django.utils import timezone


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

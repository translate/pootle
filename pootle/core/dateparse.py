#! /usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
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

from django.utils import dateparse as django_dateparse


def parse_datetime(value):
    """Parse a ISO 8601 formatted value into a date or datetime object.

    Django's own date parsing facilities differentiate date and datetime
    parsing. We need to parse dates and datetimes either way, so this is a
    convenience wrapper.

    :return: either a `datetime` or a `date` object. If the provided input
        string doesn't represent a valid date or datetime, `None` will be
        returned instead.
    """
    try:
        datetime_obj = django_dateparse.parse_datetime(value)
    except ValueError:
        datetime_obj = None

    # Not a valid datetime, check with date
    if datetime_obj is None:
        try:
            datetime_obj = django_dateparse.parse_date(value)
        except ValueError:
            datetime_obj = None

    return datetime_obj

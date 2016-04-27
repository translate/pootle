# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

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

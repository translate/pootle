# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import datetime

import pytz

from pootle.core.fields import ISODateTimeField
from pootle.core.utils.timezone import aware_datetime


def test_iso_datetime_field_no_timezone():
    """Tests parsing ISO date times without timezone information."""
    field = ISODateTimeField()
    reference_datetime = aware_datetime(2016, 9, 6, 14, 19, 52, 985000)
    parsed_datetime = field.clean('2016-09-06T14:19:52.985')
    assert isinstance(parsed_datetime, datetime.datetime)
    assert parsed_datetime == reference_datetime


def test_iso_datetime_field_utc_timezone():
    """Tests parsing ISO date times with UTC timezone information."""
    field = ISODateTimeField()
    reference_datetime = aware_datetime(2016, 9, 6, 14, 19, 52, 985000,
                                        tz=pytz.UTC)
    parsed_datetime = field.clean('2016-09-06T14:19:52.985Z')
    assert isinstance(parsed_datetime, datetime.datetime)
    assert parsed_datetime == reference_datetime


def test_iso_datetime_field_explicit_timezone():
    """Tests parsing ISO date times with a explicit timezone information."""
    field = ISODateTimeField()
    reference_datetime = aware_datetime(2016, 9, 6, 14, 19, 52, 985000,
                                        tz=pytz.timezone('Europe/Amsterdam'))
    parsed_datetime = field.clean('2016-09-06T14:19:52.985+02:00')
    assert isinstance(parsed_datetime, datetime.datetime)
    assert parsed_datetime == reference_datetime


def test_iso_datetime_field_microseconds_precision():
    """Tests the microseconds' precission after parsing.

    Microseconds have 6-digit precision as parsed by the field.
    """
    field = ISODateTimeField()
    reference_datetime = aware_datetime(2016, 9, 6, 14, 19, 52, 985,
                                        tz=pytz.UTC)
    parsed_datetime = field.clean('2016-09-06T14:19:52.985Z')
    assert isinstance(parsed_datetime, datetime.datetime)
    assert parsed_datetime != reference_datetime
    assert parsed_datetime.microsecond == 985000

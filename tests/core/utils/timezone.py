# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import datetime, timedelta

import pytest
import pytz

from django.utils import timezone

from pootle.core.utils.timezone import (
    localdate, make_aware, make_naive, aware_datetime)


def test_localdate(settings):
    today = localdate()
    assert today == timezone.localtime(timezone.now()).date()
    assert (
        localdate(timezone.now() + timedelta(weeks=1))
        == today + timedelta(weeks=1))


@pytest.mark.django_db
def test_make_aware(settings):
    """Tests datetimes can be made aware of timezones."""
    settings.USE_TZ = True

    datetime_object = datetime(2016, 1, 2, 21, 52, 25)
    assert timezone.is_naive(datetime_object)
    datetime_aware = make_aware(datetime_object)
    assert timezone.is_aware(datetime_aware)


@pytest.mark.django_db
def test_make_aware_default_tz(settings):
    """Tests datetimes are made aware of the configured timezone."""
    settings.USE_TZ = True

    datetime_object = datetime(2016, 1, 2, 21, 52, 25)
    assert timezone.is_naive(datetime_object)
    datetime_aware = make_aware(datetime_object)
    assert timezone.is_aware(datetime_aware)

    # Not comparing `tzinfo` directly because that depends on the combination of
    # actual date+times
    assert datetime_aware.tzinfo.zone == timezone.get_default_timezone().zone


@pytest.mark.django_db
def test_make_aware_explicit_tz(settings):
    """Tests datetimes are made aware of the given timezone."""
    settings.USE_TZ = True

    given_timezone = pytz.timezone('Asia/Bangkok')
    datetime_object = datetime(2016, 1, 2, 21, 52, 25)
    assert timezone.is_naive(datetime_object)
    datetime_aware = make_aware(datetime_object, tz=given_timezone)
    assert timezone.is_aware(datetime_aware)

    assert datetime_aware.tzinfo.zone == given_timezone.zone


@pytest.mark.django_db
def test_make_aware_use_tz_false(settings):
    """Tests datetimes are left intact if `USE_TZ` is not in effect."""
    settings.USE_TZ = False

    datetime_object = datetime(2016, 1, 2, 21, 52, 25)
    assert timezone.is_naive(datetime_object)
    datetime_aware = make_aware(datetime_object)
    assert timezone.is_naive(datetime_aware)


@pytest.mark.django_db
def test_make_naive(settings):
    """Tests datetimes can be made naive of timezones."""
    settings.USE_TZ = True

    datetime_object = datetime(2016, 1, 2, 21, 52, 25, tzinfo=pytz.utc)
    assert timezone.is_aware(datetime_object)
    naive_datetime = make_naive(datetime_object)
    assert timezone.is_naive(naive_datetime)


@pytest.mark.django_db
def test_make_naive_default_tz(settings):
    """Tests datetimes are made naive of the configured timezone."""
    settings.USE_TZ = True
    datetime_object = timezone.make_aware(
        datetime(2016, 1, 2, 21, 52, 25),
        timezone=pytz.timezone('Europe/Helsinki'))
    assert timezone.is_aware(datetime_object)
    naive_datetime = make_naive(datetime_object)
    assert timezone.is_naive(naive_datetime)
    assert(
        naive_datetime
        == make_naive(
            datetime_object,
            tz=pytz.timezone(settings.TIME_ZONE)))


@pytest.mark.django_db
def test_make_naive_explicit_tz(settings):
    """Tests datetimes are made naive of the given timezone."""
    settings.USE_TZ = True

    datetime_object = timezone.make_aware(datetime(2016, 1, 2, 21, 52, 25),
                                          timezone=pytz.timezone('Europe/Helsinki'))
    assert timezone.is_aware(datetime_object)
    naive_datetime = make_naive(datetime_object, tz=pytz.timezone('Asia/Bangkok'))
    assert timezone.is_naive(naive_datetime)

    # Conversion from a Helsinki aware datetime to a naive datetime in Bangkok
    # should increment 5 hours (UTC+2 vs. UTC+7)
    assert naive_datetime.hour == (datetime_object.hour + 5) % 24


@pytest.mark.django_db
def test_make_naive_use_tz_false(settings):
    """Tests datetimes are left intact if `USE_TZ` is not in effect."""
    settings.USE_TZ = False

    datetime_object = datetime(2016, 1, 2, 21, 52, 25, tzinfo=pytz.utc)
    assert timezone.is_aware(datetime_object)
    naive_datetime = make_naive(datetime_object)
    assert timezone.is_aware(naive_datetime)


def test_aware_datetime(settings):
    """Tests the creation of a timezone-aware datetime."""
    datetime_object = aware_datetime(2016, 1, 2, 21, 52, 25)
    assert timezone.is_aware(datetime_object)
    assert datetime_object.tzinfo.zone == settings.TIME_ZONE


def test_aware_datetime_explicit_tz():
    """Tests the creation of a explicitly provided timezone-aware datetime."""
    new_datetime = aware_datetime(2016, 1, 2, 21, 52, 25, tz=pytz.utc)
    assert timezone.is_aware(new_datetime)
    assert new_datetime.tzinfo.zone == pytz.utc.zone

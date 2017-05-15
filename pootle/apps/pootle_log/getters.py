# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model

from pootle.core.delegate import comparable_event, grouped_events, log
from pootle.core.plugin import getter
from pootle_store.models import Store, Unit

from .utils import (
    ComparableLogEvent, GroupedEvents, Log, StoreLog, UnitLog, UserLog)


@getter(log, sender=Store)
def store_log_getter(**kwargs_):
    return StoreLog


@getter(log, sender=Unit)
def unit_log_getter(**kwargs_):
    return UnitLog


@getter(comparable_event, sender=(Log, StoreLog, UnitLog, UserLog))
def comparable_event_getter(**kwargs_):
    return ComparableLogEvent


@getter(grouped_events, sender=(Log, StoreLog, UnitLog))
def grouped_log_events_getter(**kwargs_):
    return GroupedEvents


@getter(log, sender=get_user_model())
def user_log_getter(**kwargs_):
    return UserLog

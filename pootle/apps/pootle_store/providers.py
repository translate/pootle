# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import (
    event_formatters, format_diffs, format_syncers, format_updaters, unitid)
from pootle.core.plugin import provider
from pootle_log.utils import LogEvent
from pootle_store.unit import timeline

from .diff import DiffableStore
from .models import Unit
from .syncer import StoreSyncer
from .updater import StoreUpdater
from .utils import DefaultUnitid


@provider(format_diffs)
def register_format_diffs(**kwargs_):
    return dict(default=DiffableStore)


@provider(format_syncers)
def register_format_syncers(**kwargs_):
    return dict(
        default=StoreSyncer)


@provider(format_updaters)
def register_format_updaters(**kwargs_):
    return dict(default=StoreUpdater)


@provider(unitid, sender=Unit)
def gather_unitid_providers(**kwargs_):
    return dict(default=DefaultUnitid)


@provider(event_formatters, sender=LogEvent)
def gather_event_formatters(**kwargs_):
    return dict(
        suggestion_created=timeline.SuggestionAddedEvent,
        suggestion_accepted=timeline.SuggestionAcceptedEvent,
        suggestion_rejected=timeline.SuggestionRejectedEvent,
        target_updated=timeline.TargetUpdatedEvent,
        state_changed=timeline.UnitStateChangedEvent,
        unit_created=timeline.UnitCreatedEvent,
        comment_updated=timeline.CommentUpdatedEvent,
        check_muted=timeline.CheckMutedEvent,
        check_unmuted=timeline.CheckUnmutedEvent)

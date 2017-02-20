# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import (
    format_diffs, format_syncers, format_updaters, unitid)
from pootle.core.plugin import provider

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

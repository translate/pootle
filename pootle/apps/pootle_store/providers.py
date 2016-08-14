# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import format_diffs, format_updaters
from pootle.core.plugin import provider

from .diff import DiffableStore
from .updater import StoreUpdater


@provider(format_diffs)
def register_format_diffs(**kwargs_):
    return dict(default=DiffableStore)


@provider(format_updaters)
def register_format_updaters(**kwargs_):
    return dict(default=StoreUpdater)

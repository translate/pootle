# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import data_tool, data_updater
from pootle.core.plugin import getter
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from .store_data import StoreDataTool, StoreDataUpdater
from .tp_data import TPDataTool, TPDataUpdater


@getter(data_tool, sender=Store)
def store_data_tool_getter(**kwargs_):
    return StoreDataTool


@getter(data_updater, sender=StoreDataTool)
def store_data_tool_updater_getter(**kwargs_):
    return StoreDataUpdater


@getter(data_tool, sender=TranslationProject)
def tp_data_tool_getter(**kwargs_):
    return TPDataTool


@getter(data_updater, sender=TPDataTool)
def tp_data_tool_updater_getter(**kwargs_):
    return TPDataUpdater

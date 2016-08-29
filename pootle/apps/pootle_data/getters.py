# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pootle.core.delegate import data_tool
from pootle.core.plugin import getter
from pootle_store.models import Store

from .utils import StoreDataTool


@getter(data_tool, sender=Store)
def data_tool_getter(**kwargs_):
    return StoreDataTool

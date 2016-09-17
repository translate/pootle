# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import data_tool
from pootle_data.store_data import StoreDataTool


@pytest.mark.django_db
def test_data_tool_store(store0):
    assert data_tool.get() is None
    assert data_tool.get(store0.__class__) is StoreDataTool
    assert isinstance(store0.data_tool, StoreDataTool)
    assert store0.data_tool.store is store0

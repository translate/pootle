# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from translate.storage.factory import getclass


@pytest.fixture
def unit_syncer(tp0):
    from pootle_store.constants import TRANSLATED

    store = tp0.stores.live().first()
    unit = store.units.filter(state=TRANSLATED).first()
    ttk = getclass(store)
    return unit, ttk.UnitClass

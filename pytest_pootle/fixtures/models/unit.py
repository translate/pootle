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
def unit_syncer(store0):
    from pootle_store.constants import TRANSLATED

    unit = store0.units.filter(state=TRANSLATED).first()
    ttk = getclass(store0)
    return unit, ttk.UnitClass

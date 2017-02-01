# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import frozen
from pootle_store.models import Unit


@pytest.mark.django_db
def test_frozen_unit(store0):
    unit = store0.units.first()
    frozen_unit = frozen.get(Unit)(unit)
    assert frozen_unit.source == unit.source_f
    assert frozen_unit.target == unit.target_f
    assert frozen_unit.state == unit.state
    assert frozen_unit.translator_comment == unit.getnotes(origin="translator")

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


@pytest.fixture
def unit_plural(store0):
    from pootle_store.constants import TRANSLATED
    from ...factories import UnitDBFactory

    return UnitDBFactory(
        store=store0,
        state=TRANSLATED,
        source=["%d day ago", "%d days ago"],
        target=["%d dag gelede", "%d dae gelede"]
    )


@pytest.fixture
def get_edit_unit(default):
    from pootle_store.constants import TRANSLATED
    from pootle_store.models import Store, Unit

    from ...factories import UnitDBFactory

    unit = Unit.objects.get_translatable(
        default,
        language_code='language1'
    ).filter(state=TRANSLATED).first()

    store_path = unit.store.pootle_path.replace('language1', 'language0')
    store = Store.objects.filter(pootle_path=store_path).first()
    # create unit which will be handled as alternative source
    UnitDBFactory(store=store, source_f=unit.source, state=TRANSLATED)

    return unit

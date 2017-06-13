# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import logging
import pytest

from pytest_pootle.utils import create_store


@pytest.mark.django_db
def test_store_update_new_unit_order(store0):
    new_store = store0.deserialize(store0.serialize())
    new_unit = new_store.units[1].copy()
    new_unit.source = "INSERTED UNIT"
    new_store.units = (
        [new_store.units[0], new_unit]
        + new_store.units[2:])
    store0.update(
        new_store,
        store_revision=store0.data.max_unit_revision + 1)
    assert (
        list(store0.units.values_list("unitid", flat=True))
        == [u.getid() for u in new_store.units[1:]])


@pytest.mark.django_db
def test_store_update_with_obsolete(store_po):
    units = [('source1', 'target1', False)]
    file_store = create_store(store_po.pootle_path, units=units)
    store_po.update(file_store)
    unit = store_po.units[0]
    assert not unit.isobsolete()
    file_store.units[1].makeobsolete()
    store_po.update(file_store)
    unit = store_po.UnitClass.objects.get(id=unit.id)
    assert unit.isobsolete()


@pytest.mark.django_db
def test_store_update_with_duplicate(store_po, caplog):
    units = [
        ('source1', 'target1', False),
        ('source2', 'target2', False),
        ('source2', 'target2', False)]
    file_store = create_store(store_po.pootle_path, units=units)
    caplog.set_level(logging.WARN)
    store_po.update(file_store)
    assert (
        caplog.records[0].message
        == ('[diff] Duplicate unit found: %s source2'
            % store_po.name))

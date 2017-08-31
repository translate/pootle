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

from pootle_store.constants import POOTLE_WINS, SOURCE_WINS


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
    store_po.update(
        file_store, store_revision=store_po.data.max_unit_revision)
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


@pytest.mark.django_db
def test_store_update_conflict_fs_wins(store0, caplog):
    unit0 = store0.units[0]
    unit0.target = "foo0"
    unit0.save()

    unit1 = store0.units[1]
    unit1.target = "foo1"
    unit1.save()

    last_revision = store0.data.max_unit_revision
    ttk = store0.deserialize(store0.serialize())

    unit0.refresh_from_db()
    unit0.target = "bar0"
    unit0.save()

    fsunit0 = ttk.findid(unit0.getid())
    fsunit0.target = "baz0"

    store0.update(ttk, store_revision=last_revision, resolve_conflict=SOURCE_WINS)
    unit0.refresh_from_db()
    unit1.refresh_from_db()
    # only the fs change is updated
    assert unit0.target == "baz0"
    assert unit1.target == "foo1"


@pytest.mark.django_db
def test_store_update_conflict_pootle_wins(store0, caplog):
    unit0 = store0.units[0]
    unit0.target = "foo0"
    unit0.save()

    unit1 = store0.units[1]
    unit1.target = "foo1"
    unit1.save()

    unit2 = store0.units[2]

    last_revision = store0.data.max_unit_revision
    ttk = store0.deserialize(store0.serialize())

    unit0.refresh_from_db()
    unit0.target = "bar0"
    unit0.save()

    fsunit0 = ttk.findid(unit0.getid())
    fsunit0.target = "baz0"

    fsunit2 = ttk.findid(unit2.getid())
    fsunit2.target = "baz2"

    store0.update(ttk, store_revision=last_revision, resolve_conflict=POOTLE_WINS)
    unit0.refresh_from_db()
    unit1.refresh_from_db()
    unit2.refresh_from_db()
    assert unit0.target == "bar0"
    assert unit1.target == "foo1"
    assert unit2.target == "baz2"

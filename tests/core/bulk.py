# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.bulk import BulkCRUD
from pootle_data.models import StoreChecksData
from pootle_store.models import Unit


def test_bulk_crud_instance():

    class ExampleBulkCRUD(BulkCRUD):
        model = Unit

    unit_crud = ExampleBulkCRUD()
    assert repr(unit_crud) == "<ExampleBulkCRUD:%s>" % str(Unit._meta)
    assert unit_crud.qs == Unit.objects


@pytest.mark.django_db
def test_bulk_crud_bulk_update_method(store0):
    unit0, unit1 = store0.units[:2]

    class ExampleBulkCRUD(BulkCRUD):
        model = Unit

    unit_crud = ExampleBulkCRUD()

    unit0.target = "FOO"
    unit1.target = "BAR"
    unit_crud.bulk_update([unit0, unit1])
    unit0.refresh_from_db()
    unit1.refresh_from_db()
    assert unit0.target == "FOO"
    assert unit1.target == "BAR"

    unit0.context = "FOO CONTEXT"
    unit0.target = "NOT FOO"
    unit1.target = "NOT BAR"
    unit_crud.bulk_update(
        [unit0, unit1],
        fields=["context"])
    unit0.refresh_from_db()
    unit1.refresh_from_db()
    assert unit0.target == "FOO"
    assert unit1.target == "BAR"
    assert unit0.context == "FOO CONTEXT"


@pytest.mark.django_db
def test_bulk_crud_create_delete(store0):
    checkdata0 = StoreChecksData(
        store=store0, name="foo", category=2)

    class ExampleBulkCRUD(BulkCRUD):
        model = StoreChecksData

    checkdata_crud = ExampleBulkCRUD()

    checkdata_crud.create(instance=checkdata0)
    assert checkdata0.pk

    checkdata1 = StoreChecksData(
        store=store0, name="bar", category=2)
    checkdata2 = StoreChecksData(
        store=store0, name="baz", category=2)
    checkdata_crud.create(
        objects=[checkdata1, checkdata2])
    checkdata1 = StoreChecksData.objects.get(
        store=store0, name="bar", category=2)
    checkdata2 = StoreChecksData.objects.get(
        store=store0, name="baz", category=2)
    assert checkdata1
    assert checkdata2

    checkdata_crud.delete(instance=checkdata2)

    with pytest.raises(StoreChecksData.DoesNotExist):
        checkdata2.refresh_from_db()

    checkdata_crud.delete(
        objects=StoreChecksData.objects.filter(
            id__in=[checkdata0.id, checkdata1.id]))

    for checkdata in [checkdata0, checkdata1]:
        with pytest.raises(StoreChecksData.DoesNotExist):
            checkdata.refresh_from_db()


@pytest.mark.django_db
def test_bulk_crud_update_methods(store0):
    unit0, unit1, unit2 = store0.units[:3]

    class ExampleBulkCRUD(BulkCRUD):
        model = Unit

    unit_crud = ExampleBulkCRUD()

    updates = {
        unit0.id: dict(
            target_f="FOO",
            context="FOO CONTEXT"),
        unit1.id: dict(target_f="BAR")}

    objects = []
    result = sorted(
        unit_crud.update_objects(
            [unit0],
            updates,
            objects))
    assert result == ["context", "target_f"]
    assert objects == [unit0]
    assert unit0.target_f == "FOO"
    assert unit0.context == "FOO CONTEXT"
    result = list(
        unit_crud.update_objects(
            [unit1, unit2],
            updates,
            objects))
    assert result == ["target_f"]
    assert objects == [unit0, unit1, unit2]
    assert unit1.target_f == "BAR"

    objects = [3, 4, 5]
    result = list(
        unit_crud.update_objects(
            iter([1, 2, 3]), None, objects))
    assert objects == [3, 4, 5, 1, 2, 3]
    assert result == []

    updates = dict(store0.units.values_list("id", "unitid_hash"))
    fetched = unit_crud.objects_to_fetch([unit0, unit1, unit2], updates)
    assert (
        sorted(fetched.values_list("id", flat=True))
        == sorted(
            store0.units.exclude(
                id__in=[
                    unit0.id,
                    unit1.id,
                    unit2.id]).values_list("id", flat=True)))
    updates = {
        unit0.id: dict(
            target_f="BAR",
            context="BAR CONTEXT"),
        unit1.id: dict(target_f="BAZ")}
    objects, fields = unit_crud.update_object_list(
        objects=[unit0, unit1, unit2],
        updates=updates,
        update_fields=["field0", "field1"])
    assert (
        sorted(fields)
        == ["context", "field0", "field1", "target_f"])
    assert objects == [unit0, unit1, unit2]

    objects = [unit0, unit1]
    fields = unit_crud.update_object_dict(objects, updates, set())
    assert objects == [unit0, unit1]
    assert fields is None
    updates = {
        unit0.id: dict(target_f="FOO"),
        unit2.id: dict(developer_comment="Are we done yet?")}
    result = unit_crud.update_object_dict(objects, updates, set())
    assert objects == [unit0, unit1, unit2]
    assert result is None
    # unit0 not updated
    assert unit0.target_f == "BAR"
    assert objects[2].developer_comment == "Are we done yet?"


@pytest.mark.django_db
def test_bulk_crud_update(store0):
    unit0, unit1, unit2 = store0.units[:3]

    class ExampleBulkCRUD(BulkCRUD):
        model = Unit
        kwargs = None

        def update_common_objects(self, ids, values):
            self.ids = ids
            self.values = values
            return 23

        def bulk_update(self, objects, fields):
            self.objects = objects
            self.fields = fields
            return 77

    unit_crud = ExampleBulkCRUD()
    result = unit_crud.update(
        **dict(
            updates={unit1.id: dict(foo=1, bar=2)}))
    assert result == 23
    assert unit_crud.ids == [unit1.id]
    assert unit_crud.values == dict(foo=1, bar=2)

    unit_crud = ExampleBulkCRUD()
    result = unit_crud.update(objects=[unit0, unit1, unit2])
    assert result == 77 + len(unit_crud.objects)
    assert unit_crud.objects == [unit0, unit1, unit2]
    assert unit_crud.fields is None

    unit0.target = "THE END"
    unit_crud.update(instance=unit0)
    unit0.refresh_from_db()
    assert unit0.target == "THE END"


@pytest.mark.django_db
def test_bulk_crud_update_common(store0):
    unit0, unit1, unit2 = store0.units[:3]

    class ExampleBulkCRUD(BulkCRUD):
        model = Unit
        kwargs = None

    unit_crud = ExampleBulkCRUD()

    common_dict = dict(foo="FOO", bar="BAR")
    updates = {
        i: common_dict.copy()
        for i in range(0, 20)}
    result = unit_crud.all_updates_common(updates=updates)
    assert result == common_dict
    updates[19]["foo"] = "NOTFOO"
    result = unit_crud.all_updates_common(updates=updates)
    assert not result
    updates[19]["foo"] = "FOO"
    updates[20] = common_dict.copy()
    result = unit_crud.all_updates_common(updates=updates)
    assert result == common_dict
    del updates[20]["bar"]
    result = unit_crud.all_updates_common(updates=updates)
    assert not result
    updates[20]["bar"] = "BAR"
    result = unit_crud.all_updates_common(updates=updates)
    assert result == common_dict
    del updates[20]["bar"]
    updates[20]["baz"] = "BAR"
    result = unit_crud.all_updates_common(updates=updates)
    assert not result
    result = unit_crud.update_common_objects(
        [unit0.id, unit1.id],
        values=dict(target_f="FOO TARGET", context="FOO CONTEXT"))
    unit0.refresh_from_db()
    unit1.refresh_from_db()
    unit2.refresh_from_db()
    for unit in [unit0, unit1]:
        assert unit.target == "FOO TARGET"
        assert unit.context == "FOO CONTEXT"
    assert unit2.target != "FOO TARGET"
    assert unit2.context != "FOO CONTEXT"
    assert result == 2

    new_values = dict(target_f="BAR TARGET", context="BAR CONTEXT")
    result = unit_crud.update(
        updates={
            unit.id: new_values.copy()
            for unit
            in [unit0, unit1, unit2]})
    unit0.refresh_from_db()
    unit1.refresh_from_db()
    unit2.refresh_from_db()
    for unit in [unit0, unit1, unit2]:
        assert unit.target == "BAR TARGET"
        assert unit.context == "BAR CONTEXT"
    assert result == 3

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.dispatch import receiver

from pootle.core.contextmanagers import bulk_operations, keep_data
from pootle.core.signals import create, delete, update, update_data
from pootle_data.models import StoreChecksData
from pootle_store.models import QualityCheck, Store, Unit


def qs_match(qs1, qs2):
    return (
        list(qs1.order_by("id").values_list("id", flat=True))
        == list(qs2.order_by("id").values_list("id", flat=True)))


@pytest.mark.django_db
def test_contextmanager_keep_data(store0, no_update_data):

    result = []

    with no_update_data():

        @receiver(update_data, sender=Store)
        def update_data_handler(**kwargs):
            store = kwargs["instance"]
            result.append(store)

        update_data.send(Store, instance=store0)
        assert result == [store0]

        result.remove(store0)

        # with keep_data decorator signal is suppressed
        with keep_data():
            update_data.send(Store, instance=store0)
        assert result == []

        # works again now
        update_data.send(Store, instance=store0)
        assert result == [store0]


def _create_qc_events(unit):
    create_instances = [
        QualityCheck(
            name=("Foo%s" % i), category=2, unit=unit)
        for i in range(0, 3)]
    for instance in create_instances:
        create.send(
            QualityCheck,
            instance=instance)
    create_objects = [
        QualityCheck(
            name=("Bar%s" % i),
            category=2,
            unit=unit)
        for i in range(0, 3)]
    create_more_objects = [
        QualityCheck(
            name=("Baz%s" % i),
            category=2,
            unit=unit)
        for i in range(0, 3)]
    create.send(
        QualityCheck,
        objects=create_objects)
    create.send(
        QualityCheck,
        objects=create_more_objects)
    return create_instances + create_objects + create_more_objects


def _create_data_events(unit):
    create_instances = [
        StoreChecksData(
            store=unit.store,
            name="check-foo-%s" % i,
            count=i * 23)
        for i in range(0, 3)]
    for instance in create_instances:
        # add instances - these shouldnt appear in bulk operation
        create.send(
            StoreChecksData,
            instance=instance)
    create_objects = [
        StoreChecksData(
            store=unit.store,
            name="check-bar-%s" % i,
            count=i * 23)
        for i in range(0, 3)]
    create_more_objects = [
        StoreChecksData(
            store=unit.store,
            name="check-baz-%s" % i,
            count=i * 23)
        for i in range(0, 3)]
    # add 2 lots of objects
    create.send(
        StoreChecksData,
        objects=create_objects)
    create.send(
        StoreChecksData,
        objects=create_more_objects)
    return create_instances + create_objects + create_more_objects


@pytest.mark.django_db
def test_contextmanager_bulk_operations(store0):
    unit = store0.units.first()

    class Update(object):
        data_created = None
        qc_created = None
        data_called = 0
        qc_called = 0

    with keep_data(signals=[create]):
        updated = Update()

        @receiver(create, sender=QualityCheck)
        def handle_qc_create(**kwargs):
            assert "instance" not in kwargs
            updated.qc_created = kwargs["objects"]
            updated.qc_called += 1

        @receiver(create, sender=StoreChecksData)
        def handle_data_create(**kwargs):
            updated.data_called += 1
            if "objects" in kwargs:
                updated.data_created = kwargs["objects"]
            else:
                assert "instance" in kwargs

        with bulk_operations(QualityCheck):
            qc_creates = _create_qc_events(unit)
            data_creates = _create_data_events(unit)
        assert updated.qc_created == qc_creates
        assert updated.qc_called == 1
        assert updated.data_created != data_creates
        assert updated.data_called == 5

        # nested update
        updated = Update()
        with bulk_operations(QualityCheck):
            with bulk_operations(QualityCheck):
                qc_creates = _create_qc_events(unit)
                data_creates = _create_data_events(unit)
        assert updated.qc_created == qc_creates
        assert updated.qc_called == 1
        assert updated.data_created != data_creates
        assert updated.data_called == 5

        # nested update - different models
        updated = Update()
        with bulk_operations(StoreChecksData):
            with bulk_operations(QualityCheck):
                qc_creates = _create_qc_events(unit)
                data_creates = _create_data_events(unit)
        assert updated.qc_created == qc_creates
        assert updated.qc_called == 1
        assert updated.data_created == data_creates
        assert updated.data_called == 1

        updated = Update()
        with bulk_operations(models=(StoreChecksData, QualityCheck)):
            qc_creates = _create_qc_events(unit)
            data_creates = _create_data_events(unit)
        assert updated.qc_created == qc_creates
        assert updated.qc_called == 1
        assert updated.data_created == data_creates
        assert updated.data_called == 1


@pytest.mark.django_db
def test_contextmanager_bulk_ops_delete(tp0, store0):
    unit = store0.units.first()
    store1 = tp0.stores.filter(name="store1.po").first()
    store2 = tp0.stores.filter(name="store2.po").first()

    class Update(object):
        store_deleted = None
        unit_deleted = None
        store_called = 0
        unit_called = 0

    with keep_data(signals=[delete]):
        updated = Update()

        @receiver(delete, sender=Unit)
        def handle_unit_delete(**kwargs):
            assert "instance" not in kwargs
            updated.unit_deleted = kwargs["objects"]
            updated.unit_called += 1

        @receiver(delete, sender=Store)
        def handle_store_delete(**kwargs):
            updated.store_called += 1
            if "objects" in kwargs:
                updated.store_deleted = kwargs["objects"]
            else:
                assert "instance" in kwargs

        with bulk_operations(Unit):
            delete.send(Unit, instance=unit)
            delete.send(Unit, objects=store1.unit_set.all())
            delete.send(Unit, objects=store2.unit_set.all())
            delete.send(Store, instance=store0)
            delete.send(
                Store,
                objects=store1.translation_project.stores.filter(
                    id=store1.id))
            delete.send(
                Store,
                objects=store2.translation_project.stores.filter(
                    id=store2.id))
        assert updated.unit_called == 1
        assert qs_match(
            updated.unit_deleted,
            (store0.unit_set.filter(id=unit.id)
             | store1.unit_set.all()
             | store2.unit_set.all()))
        assert updated.store_called == 3


@pytest.mark.django_db
def test_contextmanager_bulk_ops_update(tp0, store0):
    unit = store0.units.first()
    store1 = tp0.stores.filter(name="store1.po").first()
    store2 = tp0.stores.filter(name="store2.po").first()

    class Update(object):
        store_updated = None
        unit_updated = None
        store_called = 0
        unit_called = 0
        unit_updates = None

    with keep_data(signals=[update]):
        updated = Update()

        @receiver(update, sender=Unit)
        def handle_unit_update(**kwargs):
            assert "instance" not in kwargs
            updated.unit_updated = kwargs["objects"]
            updated.unit_called += 1
            updated.unit_update_fields = kwargs.get("update_fields")
            updated.unit_updates = kwargs.get("updates")

        @receiver(update, sender=Store)
        def handle_store_update(**kwargs):
            updated.store_called += 1
            if "objects" in kwargs:
                updated.store_updated = kwargs["objects"]
            else:
                assert "instance" in kwargs

        with bulk_operations(Unit):
            update.send(Unit, instance=unit)
            update.send(Unit, objects=list(store1.unit_set.all()))
            update.send(Unit, objects=list(store2.unit_set.all()))
            update.send(Unit, update_fields=set(["foo", "bar"]))
            update.send(Unit, update_fields=set(["bar", "baz"]))
            update.send(Store, instance=store0)
            update.send(
                Store,
                objects=list(store1.translation_project.stores.filter(
                    id=store1.id)))
            update.send(
                Store,
                objects=list(store2.translation_project.stores.filter(
                    id=store2.id)))
        assert updated.unit_called == 1
        assert isinstance(updated.unit_updated, list)
        assert qs_match(
            Unit.objects.filter(
                id__in=(
                    un.id for un in updated.unit_updated)),
            (store0.unit_set.filter(id=unit.id)
             | store1.unit_set.all()
             | store2.unit_set.all()))
        assert updated.store_called == 3
        assert updated.unit_update_fields == set(["bar", "baz", "foo"])

        updated = Update()
        d1 = {23: dict(foo=True), 45: dict(bar=False)}
        d2 = {67: dict(baz=89)}
        with bulk_operations(Unit):
            update.send(Unit, updates=d1)
            update.send(Unit, updates=d2)
        d1.update(d2)
        assert updated.unit_updates == d1

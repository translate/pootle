#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest


@pytest.mark.django_db
def test_delete_mark_obsolete(af_tutorial_subdir_po):
    """Tests that the in-DB Store and Directory are marked as obsolete
    after the on-disk file ceased to exist.

    Refs. #269.
    """
    from pootle_store.models import Store, Unit

    tp = af_tutorial_subdir_po.translation_project
    pootle_path = af_tutorial_subdir_po.pootle_path

    # Scan TP files and parse units
    tp.scan_files()
    for store in tp.stores.all():
        store.update(overwrite=False, only_newer=False)

    # Remove on-disk file
    os.remove(af_tutorial_subdir_po.file.path)

    # Update stores by rescanning TP
    tp.scan_files()

    # Now files that ceased to exist should be marked as obsolete
    updated_store = Store.objects.get(pootle_path=pootle_path)
    assert updated_store.obsolete

    # The units they contained are obsolete too
    store_units = Unit.objects.filter(store=updated_store)
    for unit in store_units:
        assert unit.isobsolete()


@pytest.mark.django_db
def test_sync(fr_tutorial_remove_sync_po):
    """Tests that the new on-disk file is created after sync for existing
    in-DB Store if the corresponding on-disk file ceased to exist.
    """

    tp = fr_tutorial_remove_sync_po.translation_project
    pootle_path = fr_tutorial_remove_sync_po.pootle_path

    # Parse stores
    for store in tp.stores.all():
        store.update(overwrite=False, only_newer=False)

    assert fr_tutorial_remove_sync_po.file.exists()
    os.remove(fr_tutorial_remove_sync_po.file.path)

    from pootle_store.models import Store
    store = Store.objects.get(pootle_path=pootle_path)
    assert not store.file.exists()
    store.sync()
    assert store.file.exists()


@pytest.mark.django_db
def test_update(ru_tutorial_po):
    """Tests unit order after a specific update.
    """

    tp = ru_tutorial_po.translation_project
    pootle_path = ru_tutorial_po.pootle_path

    # Parse stores
    ru_tutorial_po.update(overwrite=False, only_newer=False)

    print ru_tutorial_po.file
    assert ru_tutorial_po.file.exists()

    # check if initial indexing is correct
    old_unit_order = {'first': 1, 'second': 2, 'third': 3}
    for unit in ru_tutorial_po.units:
        assert old_unit_order[unit.unitid] == unit.index

    ru_tutorial_po.file = 'tutorial/ru/tutorial_updated.po'
    ru_tutorial_po.update(overwrite=False, only_newer=False)

    # check if updated indexing is correct
    new_unit_order = {'before first': 1, 'first': 2, 'third': 4}
    for unit in ru_tutorial_po.units:
        assert new_unit_order[unit.unitid] == unit.index

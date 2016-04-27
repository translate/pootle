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
def test_delete_mark_obsolete_resurrect_sync(fr_tutorial_subdir_to_remove_po):
    """Tests that the in-DB Directory are marked as obsolete
    after the on-disk file ceased to exist and that the on-disk file and
    directory are recovered after syncing.

    Refs. #269.
    """
    from pootle_app.models.directory import Directory
    from pootle_store.models import Store, Unit

    tp = fr_tutorial_subdir_to_remove_po.translation_project
    dir_pootle_path = fr_tutorial_subdir_to_remove_po.parent.pootle_path
    store_pootle_path = fr_tutorial_subdir_to_remove_po.pootle_path

    # Parse stores
    for store in tp.stores.all():
        store.update(store.file.store)

    # Remove on-disk directory
    os.remove(fr_tutorial_subdir_to_remove_po.file.path)
    af_tutorial_subdir_to_remove = \
        os.path.dirname(fr_tutorial_subdir_to_remove_po.file.path)
    os.rmdir(af_tutorial_subdir_to_remove)

    # Update stores by rescanning TP
    tp.scan_files()

    # Now files and directories that ceased to exist should be marked as
    # obsolete
    updated_directory = Directory.objects.get(pootle_path=dir_pootle_path)
    assert updated_directory.obsolete

    updated_store = Store.objects.get(pootle_path=store_pootle_path)
    assert updated_store.obsolete

    # The units they contained are obsolete too
    store_units = Unit.objects.filter(store=updated_store)
    for unit in store_units:
        assert unit.isobsolete()

    # Resurrect directory
    updated_directory.obsolete = False
    updated_directory.save()
    # Resurrect store
    updated_store.obsolete = False
    updated_store.save()
    # Resurrect units
    for unit in store_units:
        unit.resurrect()
        unit.save()

    # Recover store and directory by syncing
    updated_store.sync(only_newer=False)
    # Now file and directory for the store should exist
    assert os.path.exists(updated_store.file.path)


@pytest.mark.django_db
def test_scan_empty_project_obsolete_dirs(es_tutorial_subdir_remove_po):
    """Tests that the in-DB Directories are marked as obsolete
    if the on-disk directories are empty.
    """
    spanish_tutorial = es_tutorial_subdir_remove_po.translation_project
    os.remove(es_tutorial_subdir_remove_po.file.path)

    spanish_tutorial.scan_files()
    for item in spanish_tutorial.directory.child_dirs.all():
        assert item.obsolete

    assert spanish_tutorial.directory.obsolete

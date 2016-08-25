# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil

import pytest
from pytest_pootle.factories import DirectoryFactory

from django.dispatch import receiver

from pootle.core.signals import object_obsoleted
from pootle_app.models import Directory
from pootle_store.models import Store, Unit
from pootle_translationproject.models import TranslationProject


@pytest.mark.django_db
def test_delete_mark_obsolete_resurrect_sync(project0_nongnu, subdir0):
    """Tests that the in-DB Directory are marked as obsolete
    after the on-disk file ceased to exist and that the on-disk file and
    directory are recovered after syncing.

    Refs. #269.
    """
    store = subdir0.child_stores.first()
    store.sync()
    tp = store.translation_project
    dir_pootle_path = store.parent.pootle_path
    store_pootle_path = store.pootle_path

    # Sync stores
    for _store in tp.stores.all():
        _store.sync()

    # Remove on-disk directory
    os.remove(store.file.path)
    shutil.rmtree(os.path.dirname(store.file.path))

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
def test_scan_empty_project_obsolete_dirs(project0_nongnu, store0):
    """Tests that the in-DB Directories are marked as obsolete
    if the on-disk directories are empty.
    """
    tp = store0.translation_project

    tp.scan_files()
    for item in tp.directory.child_dirs.all():
        assert item.obsolete

    assert tp.directory.obsolete


@pytest.mark.django_db
def test_directory_obsolete_signal(cleanup_receivers):
    tp = TranslationProject.objects.get(
        language__code="language0", project__code="project0")

    directory = DirectoryFactory(name="signal_directory", parent=tp.directory)

    class ResultHandler(object):
        pass

    results = ResultHandler()

    @receiver(object_obsoleted, sender=Directory)
    def handle_object_obsolete(**kwargs):
        kwargs["foo"] = "bar"
        results.kwargs = kwargs

    directory.makeobsolete()
    assert results.kwargs["foo"] == "bar"
    assert results.kwargs["instance"] is directory
    assert results.kwargs["sender"] is Directory

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

from django.core.exceptions import ValidationError

from pootle_app.models.directory import Directory
from pootle_store.models import Store


@pytest.mark.django_db
def test_directory_create_name_with_slashes_or_backslashes(root):
    """Test Directories are not created with (back)slashes on their name."""

    with pytest.raises(ValidationError):
        Directory.objects.create(name="slashed/name", parent=root)

    with pytest.raises(ValidationError):
        Directory.objects.create(name="backslashed\\name", parent=root)


@pytest.mark.django_db
def test_directory_create_bad(root):
    """Test directory cannot be created with name and no parent or without name
    but no parent.
    """
    with pytest.raises(ValidationError):
        Directory.objects.create(name="name", parent=None)

    with pytest.raises(ValidationError):
        Directory.objects.create(name="", parent=root)


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

    # Resurrect directory
    updated_directory.obsolete = False
    updated_directory.save()
    # Resurrect store
    updated_store.obsolete = False
    updated_store.save()

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
def test_dir_get_or_make_subdir(project0, language0, tp0, subdir0):
    foo = project0.directory.get_or_make_subdir("foo")
    assert not foo.tp
    assert foo == project0.directory.get_or_make_subdir("foo")

    foo = language0.directory.get_or_make_subdir("foo")
    assert not foo.tp
    assert foo == language0.directory.get_or_make_subdir("foo")

    foo = tp0.directory.get_or_make_subdir("foo")
    assert foo.tp == tp0
    assert foo == tp0.directory.get_or_make_subdir("foo")

    foo = subdir0.get_or_make_subdir("foo")
    assert foo.tp == subdir0.tp
    assert foo == subdir0.get_or_make_subdir("foo")

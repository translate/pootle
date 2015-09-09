#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import time

import pytest

from django.core.files.uploadedfile import SimpleUploadedFile

from translate.storage.factory import getclass
from pootle.core.models import Revision
from pootle_statistics.models import SubmissionTypes
from pootle_store.models import NEW, PARSED, Store

from .unit import _update_translation


def _update_from_upload_file(tutorial, update_file,
                             content_type="text/x-gettext-translation",
                             user=None, submission_type=None):
    with open(update_file, "r") as f:
        upload = SimpleUploadedFile(os.path.basename(update_file),
                                    f.read(),
                                    content_type)
    test_store = getclass(upload)(upload.read())
    tutorial.update(overwrite=False, only_newer=False)
    tutorial.update(overwrite=True, store=test_store,
                    user=user, submission_type=submission_type)


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
def test_update_unit_order(ru_tutorial_po):
    """Tests unit order after a specific update.
    """

    # Parse stores
    ru_tutorial_po.update(overwrite=False, only_newer=False)
    # Set last sync revision
    ru_tutorial_po.sync()

    print ru_tutorial_po.file
    assert ru_tutorial_po.file.exists()

    old_unit_list = ['1->2', '2->4', '3->3', '4->5']
    updated_unit_list = list(
        [unit.unitid for unit in ru_tutorial_po.units]
    )
    assert old_unit_list == updated_unit_list

    ru_tutorial_po.file = 'tutorial/ru/tutorial_updated.po'
    ru_tutorial_po.update(overwrite=False, only_newer=False)

    old_unit_list = ['X->1', '1->2', '3->3', '2->4', '4->5', 'X->6', 'X->7', 'X->8']
    updated_unit_list = list(
        [unit.unitid for unit in ru_tutorial_po.units]
    )
    assert old_unit_list == updated_unit_list


@pytest.mark.django_db
def test_update_save_changed_units(ru_update_save_changed_units_po):
    """Tests that any update saves changed units only.
    """
    store = ru_update_save_changed_units_po

    store.update(overwrite=False, only_newer=False)
    unit_list = list(store.units)
    # Set last sync revision
    store.sync()

    # delay for 1 sec, we'll compare mtimes
    time.sleep(1)
    store.file = 'tutorial/ru/update_save_changed_units_updated.po'
    store.update(overwrite=False, only_newer=False)
    updated_unit_list = list(store.units)

    for index in range(0, len(unit_list)):
        unit = unit_list[index]
        updated_unit = updated_unit_list[index]
        if unit.target == updated_unit.target:
            assert unit.revision == updated_unit.revision
            assert unit.mtime == updated_unit.mtime


@pytest.mark.django_db
def test_update_set_last_sync_revision(ru_update_set_last_sync_revision_po):
    """Tests setting last_sync_revision after store creation.
    """
    store = ru_update_set_last_sync_revision_po

    # Parse a store during first update
    # store.last_sync_revision is set to the next global revision
    next_revision = Revision.get() + 1
    store.update(overwrite=False, only_newer=False)
    assert store.last_sync_revision == next_revision
    assert store.get_max_unit_revision() == next_revision

    # store.last_sync_revision is not changed after empty update
    store.update(overwrite=False, only_newer=False)
    assert store.last_sync_revision == next_revision

    # any non-empty update sets last_sync_revision to next global revision
    store.file = 'tutorial/ru/update_set_last_sync_revision_updated.po'
    next_revision = Revision.get() + 1
    store.update(overwrite=False, only_newer=False)
    assert store.last_sync_revision == next_revision

    # store.last_sync_revision is not changed after empty update
    # (even if it has unsynced units)
    item_index = 0
    next_unit_revision = Revision.get() + 1
    dbunit = _update_translation(store, item_index, {'target': u'first'},
                                 sync=False)
    assert dbunit.revision == next_unit_revision
    store.update(overwrite=False, only_newer=False)
    assert store.last_sync_revision == next_revision

    # Non-empty update sets store.last_sync_revision to next global revision
    # (even the store has unsynced units)
    # There is only one unsynced unit in this case so its revision should be set
    # next to store.last_sync_revision
    next_revision = Revision.get() + 1
    store.file = 'tutorial/ru/update_set_last_sync_revision.po'
    store.update(overwrite=False, only_newer=False)
    assert store.last_sync_revision == next_revision
    unit = store.getitem(item_index)
    assert unit.revision == store.last_sync_revision + 1


@pytest.mark.django_db
def test_update_upload_defaults(en_tutorial_po, system):
    _update_from_upload_file(en_tutorial_po,
                             "tests/data/po/tutorial/en/tutorial_update.po")
    assert en_tutorial_po.units[0].submitted_by == system
    assert (en_tutorial_po.units[0].submission_set.first().type
            == SubmissionTypes.SYSTEM)


@pytest.mark.django_db
def test_update_upload_member_user(en_tutorial_po, member):
    _update_from_upload_file(en_tutorial_po,
                             "tests/data/po/tutorial/en/tutorial_update.po",
                             user=member)
    assert en_tutorial_po.units[0].submitted_by == member


@pytest.mark.django_db
def test_update_upload_submission_type(en_tutorial_po):
    _update_from_upload_file(en_tutorial_po,
                             "tests/data/po/tutorial/en/tutorial_update.po",
                             submission_type=SubmissionTypes.UPLOAD)
    assert (en_tutorial_po.units[0].submission_set.first().type
            == SubmissionTypes.UPLOAD)


@pytest.mark.django_db
def test_update_upload_new_revision(en_tutorial_po):
    _update_from_upload_file(en_tutorial_po,
                             "tests/data/po/tutorial/en/tutorial_update.po",
                             submission_type=SubmissionTypes.UPLOAD)
    assert en_tutorial_po.units[0].target == "Hello, world UPDATED"


@pytest.mark.django_db
def test_update_upload_again_new_revision(en_tutorial_po):
    assert en_tutorial_po.state == NEW
    _update_from_upload_file(en_tutorial_po,
                             "tests/data/po/tutorial/en/tutorial_update.po",
                             submission_type=SubmissionTypes.UPLOAD)
    store = Store.objects.get(pk=en_tutorial_po.pk)
    assert store.state == PARSED
    assert store.units[0].target == "Hello, world UPDATED"
    _update_from_upload_file(store,
                             "tests/data/po/tutorial/en/tutorial_update_again.po",
                             submission_type=SubmissionTypes.UPLOAD)
    store = Store.objects.get(pk=en_tutorial_po.pk)
    assert store.state == PARSED
    assert store.units[0].target == "Hello, world UPDATED AGAIN"


@pytest.mark.django_db
def test_update_upload_old_revision_unit_conflict(en_tutorial_po):
    _update_from_upload_file(en_tutorial_po,
                             "tests/data/po/tutorial/en/tutorial_update.po")

    # load update with expired revision and conflicting unit
    file_name = "tests/data/po/tutorial/en/tutorial_update_conflict.po"
    _update_from_upload_file(en_tutorial_po, file_name)

    # unit target is not updated
    assert en_tutorial_po.units[0].target == "Hello, world UPDATED"

    # but suggestion is added
    suggestion = en_tutorial_po.units[0].get_suggestions()[0].target
    assert suggestion == "Hello, world CONFLICT"


@pytest.mark.django_db
def test_update_upload_new_revision_new_unit(en_tutorial_po):
    file_name = "tests/data/po/tutorial/en/tutorial_update_new_unit.po"
    _update_from_upload_file(en_tutorial_po, file_name)

    # the new unit has been added
    assert en_tutorial_po.units[1].target == 'Goodbye, world'


@pytest.mark.django_db
def test_update_upload_old_revision_new_unit(en_tutorial_po):
    # load initial update
    _update_from_upload_file(en_tutorial_po,
                             "tests/data/po/tutorial/en/tutorial_update.po")

    # load old revision with new unit
    file_name = "tests/data/po/tutorial/en/tutorial_update_old_unit.po"
    _update_from_upload_file(en_tutorial_po, file_name)

    # the new unit has not been added
    assert len(en_tutorial_po.units) == 1

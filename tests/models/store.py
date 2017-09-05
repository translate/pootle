# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import io
import os

import six

import pytest

from pytest_pootle.factories import (
    LanguageDBFactory, ProjectDBFactory, StoreDBFactory,
    TranslationProjectFactory)
from pytest_pootle.utils import update_store

from translate.storage.factory import getclass

from django.db.models import Max
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from pootle.core.delegate import (
    config, format_classes, format_diffs, formats)
from pootle.core.models import Revision
from pootle.core.delegate import deserializers, serializers
from pootle.core.url_helpers import to_tp_relative_path
from pootle.core.plugin import provider
from pootle.core.serializers import Serializer, Deserializer
from pootle_app.models import Directory
from pootle_config.exceptions import ConfigurationError
from pootle_format.exceptions import UnrecognizedFiletype
from pootle_format.formats.po import PoStoreSyncer
from pootle_format.models import Format
from pootle_fs.utils import FSPlugin
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_statistics.models import (
    SubmissionFields, SubmissionTypes)
from pootle_store.constants import (
    NEW, OBSOLETE, PARSED, POOTLE_WINS, TRANSLATED)
from pootle_store.diff import DiffableStore, StoreDiff
from pootle_store.models import Store
from pootle_store.util import parse_pootle_revision
from pootle_translationproject.models import TranslationProject


def _update_from_upload_file(store, update_file,
                             content_type="text/x-gettext-translation",
                             user=None, submission_type=None):
    with open(update_file, "r") as f:
        upload = SimpleUploadedFile(os.path.basename(update_file),
                                    f.read(),
                                    content_type)
    test_store = getclass(upload)(upload.read())
    store_revision = parse_pootle_revision(test_store)
    store.update(test_store, store_revision=store_revision,
                 user=user, submission_type=submission_type)


def _store_as_string(store):
    ttk = store.syncer.convert(store.syncer.file_class)
    if hasattr(ttk, "updateheader"):
        # FIXME We need those headers on import
        # However some formats just don't support setting metadata
        ttk.updateheader(
            add=True, X_Pootle_Path=store.pootle_path)
        ttk.updateheader(
            add=True, X_Pootle_Revision=store.get_max_unit_revision())
    return str(ttk)


def _sync_store(settings, store, resolve=None, update="all", force_add=None):
    tp = store.translation_project
    project = tp.project
    language = tp.language
    plugin = FSPlugin(project)
    project.config["pootle_fs.fs_url"] = os.path.join(
        settings.POOTLE_TRANSLATION_DIRECTORY,
        project.code)
    plugin.fetch()
    if force_add:
        plugin.add(update=update, force=True)
    else:
        plugin.add(update=update)
    if resolve == "pootle_wins":
        plugin.resolve(pootle_wins=True)
    elif resolve == "fs_wins":
        plugin.resolve(pootle_wins=False)
    plugin.sync(update=update)
    return os.path.join(
        plugin.fs_url,
        language.code,
        store.name)


@pytest.mark.django_db
def test_sync(project0_nongnu, project0, store0, settings):
    """Tests that the new on-disk file is created after sync for existing
    in-DB Store if the corresponding on-disk file ceased to exist.
    """
    tp = TranslationProjectFactory(
        project=project0, language=LanguageDBFactory())
    store = StoreDBFactory(
        translation_project=tp,
        parent=tp.directory)
    store.update(store.deserialize(store0.serialize()))
    file_path = _sync_store(settings, store)
    assert os.path.exists(file_path)
    os.remove(file_path)


@pytest.mark.django_db
def test_update_from_ts(store0, test_fs, member):
    store0.parsed = True
    orig_units = store0.units.count()
    existing_created_at = store0.units.aggregate(
        Max("creation_time"))["creation_time__max"]
    existing_mtime = store0.units.aggregate(
        Max("mtime"))["mtime__max"]
    old_revision = store0.data.max_unit_revision
    with test_fs.open(['data', 'ts', 'tutorial', 'en', 'tutorial.ts']) as f:
        store = getclass(f)(f.read())
    store0.update(
        store,
        submission_type=SubmissionTypes.UPLOAD,
        user=member)
    assert not store0.units[orig_units].hasplural()
    unit = store0.units[orig_units + 1]
    assert unit.submission_set.count() == 0
    assert unit.hasplural()
    assert unit.creation_time >= existing_created_at
    assert unit.creation_time >= existing_mtime
    unit_source = unit.unit_source
    assert unit_source.created_with == SubmissionTypes.UPLOAD
    assert unit_source.created_by == member
    assert unit.change.changed_with == SubmissionTypes.UPLOAD
    assert unit.change.submitted_by == member
    assert unit.change.submitted_on >= unit.creation_time
    assert unit.change.reviewed_by is None
    assert unit.change.reviewed_on is None
    assert unit.revision > old_revision


@pytest.mark.django_db
def test_update_ts_plurals(store_po, test_fs, ts):
    project = store_po.translation_project.project
    filetype_tool = project.filetype_tool
    project.filetypes.add(ts)
    filetype_tool.set_store_filetype(store_po, ts)

    with test_fs.open(['data', 'ts', 'add_plurals.ts']) as f:
        file_store = getclass(f)(f.read())
    store_po.update(file_store)
    unit = store_po.units[0]
    assert unit.hasplural()
    assert unit.submission_set.count() == 0

    with test_fs.open(['data', 'ts', 'update_plurals.ts']) as f:
        file_store = getclass(f)(f.read())
    store_po.update(
        file_store,
        store_revision=store_po.data.max_unit_revision)
    unit = store_po.units[0]
    assert unit.hasplural()
    assert unit.submission_set.count() == 1
    update_sub = unit.submission_set.first()
    assert update_sub.revision == unit.revision
    assert update_sub.creation_time == unit.change.submitted_on
    assert update_sub.submitter == unit.change.submitted_by
    assert update_sub.new_value == unit.target
    assert update_sub.type == unit.change.changed_with
    assert update_sub.field == SubmissionFields.TARGET
    # this fails 8(
    # from pootle.core.utils.multistring import unparse_multistring
    # assert (
    #      unparse_multistring(update_sub.new_value)
    #      == unparse_multistring(unit.target))


@pytest.mark.django_db
def test_update_with_non_ascii(store0, test_fs):
    store0.state = PARSED
    orig_units = store0.units.count()
    path = 'data', 'po', 'tutorial', 'en', 'tutorial_non_ascii.po'
    with test_fs.open(path) as f:
        store = getclass(f)(f.read())
    store0.update(store)
    last_unit = store0.units[orig_units]
    updated_target = "Hèḽḽě, ŵôrḽḓ"
    assert last_unit.target == updated_target
    assert last_unit.submission_set.count() == 0
    # last_unit.target = "foo"
    # last_unit.save()
    # this should now have a submission with the old target
    # but it fails
    # assert last_unit.submission_set.count() == 1
    # update_sub = last_unit.submission_set.first()
    # assert update_sub.old_value == updated_target
    # assert update_sub.new_value == "foo"


@pytest.mark.django_db
def test_update_unit_order(project0_nongnu, ordered_po,
                           ordered_update_ttk, settings):
    """Tests unit order after a specific update.
    """
    # Set last sync revision
    file_path = _sync_store(settings, ordered_po)
    assert os.path.exists(file_path)
    expected_unit_list = ['1->2', '2->4', '3->3', '4->5']
    updated_unit_list = [unit.unitid for unit in ordered_po.units]
    assert expected_unit_list == updated_unit_list
    original_revision = ordered_po.get_max_unit_revision()
    ordered_po.update(
        ordered_update_ttk,
        store_revision=original_revision)
    expected_unit_list = [
        'X->1', '1->2', '3->3', '2->4',
        '4->5', 'X->6', 'X->7', 'X->8']
    updated_unit_list = [unit.unitid for unit in ordered_po.units]
    assert expected_unit_list == updated_unit_list
    unit = ordered_po.units.first()
    assert unit.revision > original_revision
    assert unit.submission_set.count() == 0


@pytest.mark.django_db
def test_update_save_changed_units(project0_nongnu, store0, test_fs,
                                   member, system, settings):
    """Tests that any update saves changed units only.
    """
    # not sure if this is testing anything
    store = store0

    # Set last sync revision
    store.fs.all().delete()

    file_path = _sync_store(settings, store0)
    store.update(store.deserialize(open(file_path).read()))
    unit_list = list(store.units)
    update_file = test_fs.open(
        "data/po/tutorial/ru/update_save_changed_units_updated.po",
        "r")
    with update_file as sourcef:
        store.update(
            store.deserialize(sourcef.read()),
            user=member)
    updated_unit_list = list(store.units)
    # nothing changed except revisions of unsynced units
    # to ensure its synced back to fs
    for index in range(0, len(unit_list)):
        unit = unit_list[index]
        updated_unit = updated_unit_list[index]
        if unit.revision > 0:
            assert unit.revision < updated_unit.revision
        assert unit.mtime == updated_unit.mtime
        assert unit.target == updated_unit.target


@pytest.mark.django_db
def test_update_set_last_sync_revision(project0_nongnu, tp0, store0,
                                       test_fs, settings):
    """Tests setting last_sync_revision after store creation.
    """
    unit = store0.units.first()
    unit.target = "UPDATED TARGET"
    unit.save()
    file_path = _sync_store(settings, store0, resolve="pootle_wins")

    # Store is already parsed and store.last_sync_revision should be equal to
    # max unit revision
    fs = store0.fs.get()
    assert fs.last_sync_revision == store0.get_max_unit_revision()

    # store.last_sync_revision is not changed after empty update
    saved_last_sync_revision = fs.last_sync_revision
    # store0.updater.update_from_disk()
    _sync_store(settings, store0)
    fs.refresh_from_db()
    assert fs.last_sync_revision == saved_last_sync_revision

    update_file = test_fs.open(
        "data/po/tutorial/ru/update_set_last_sync_revision_updated.po",
        "r")
    with update_file as sourcef:
        with open(file_path, "wb") as targetf:
            targetf.write(sourcef.read())

    store0.refresh_from_db()
    # any non-empty update sets last_sync_revision to next global revision
    next_revision = Revision.get() + 1
    _sync_store(settings, store0)
    fs.refresh_from_db()
    assert fs.last_sync_revision == next_revision

    # store.last_sync_revision is not changed after empty update (even if it
    # has unsynced units)
    next_unit_revision = Revision.get() + 1
    dbunit = store0.units.first()
    dbunit.target = "ANOTHER DB TARGET UPDATE"
    dbunit.save()

    assert dbunit.revision == next_unit_revision

    _sync_store(settings, store0, update="pootle")
    fs.refresh_from_db()
    assert fs.last_sync_revision == next_revision

    # Non-empty update sets store.last_sync_revision to next global revision
    # (even the store has unsynced units).  There is only one unsynced unit in
    # this case so its revision should be set next to store.last_sync_revision
    dbunit = store0.units.first()
    dbunit.target = "ANOTHER DB TARGET UPDATE AGAIN"
    dbunit.save()
    next_revision = Revision.get() + 1
    orig = store0.deserialize(store0.serialize())
    orig.units[2].target = "SOMETHING ELSE"
    with open(file_path, "wb") as targetf:
        targetf.write(str(orig))
    _sync_store(settings, store0, resolve="fs_wins", update="pootle")
    fs.refresh_from_db()
    assert fs.last_sync_revision == next_revision
    # Get unsynced unit in DB. Its revision should be greater
    # than store.last_sync_revision to allow to keep this change during
    # update from a file
    dbunit.refresh_from_db()
    store0.data.refresh_from_db()
    assert store0.data.max_unit_revision == dbunit.revision
    assert dbunit.revision == fs.last_sync_revision + 1


@pytest.mark.django_db
def test_update_upload_defaults(store0, system):
    store0.state = PARSED
    unit = store0.units.first()
    original_revision = unit.revision
    last_sub_pk = unit.submission_set.order_by(
        "id").values_list("id", flat=True).last() or 0
    update_store(
        store0,
        [(unit.source, "%s UPDATED" % unit.source, False)],
        store_revision=Revision.get() + 1)
    unit = store0.units[0]
    assert unit.change.submitted_by == system
    assert unit.change.submitted_on >= unit.creation_time
    assert unit.change.submitted_by == system
    assert (
        unit.submission_set.last().type
        == SubmissionTypes.SYSTEM)
    assert unit.revision > original_revision
    new_subs = unit.submission_set.filter(id__gt=last_sub_pk).order_by("id")
    # there should be 2 new subs - state_change and target_change
    new_subs = unit.submission_set.filter(id__gt=last_sub_pk).order_by("id")
    assert new_subs.count() == 2
    target_sub = new_subs[0]
    assert target_sub.old_value == ""
    assert target_sub.new_value == unit.target
    assert target_sub.field == SubmissionFields.TARGET
    assert target_sub.type == SubmissionTypes.SYSTEM
    assert target_sub.submitter == system
    assert target_sub.revision == unit.revision
    assert target_sub.creation_time == unit.change.submitted_on
    state_sub = new_subs[1]
    assert state_sub.old_value == "0"
    assert state_sub.new_value == "200"
    assert state_sub.field == SubmissionFields.STATE
    assert state_sub.type == SubmissionTypes.SYSTEM
    assert state_sub.submitter == system
    assert state_sub.revision == unit.revision
    assert state_sub.creation_time == unit.change.submitted_on


@pytest.mark.django_db
def test_update_upload_member_user(store0, system, member):
    store0.state = PARSED
    original_unit = store0.units.first()
    original_revision = original_unit.revision
    last_sub_pk = original_unit.submission_set.order_by(
        "id").values_list("id", flat=True).last() or 0
    update_store(
        store0,
        [(original_unit.source, "%s UPDATED" % original_unit.source, False)],
        user=member,
        store_revision=Revision.get() + 1,
        submission_type=SubmissionTypes.UPLOAD)
    unit = store0.units[0]
    assert unit.change.submitted_by == member
    assert unit.change.changed_with == SubmissionTypes.UPLOAD
    assert unit.change.submitted_on >= unit.creation_time
    assert unit.change.reviewed_on is None
    assert unit.revision > original_revision
    unit_source = unit.unit_source
    unit_source.created_by == system
    unit_source.created_with == SubmissionTypes.SYSTEM
    # there should be 2 new subs - state_change and target_change
    new_subs = unit.submission_set.filter(id__gt=last_sub_pk).order_by("id")
    assert new_subs.count() == 2
    target_sub = new_subs[0]
    assert target_sub.old_value == ""
    assert target_sub.new_value == unit.target
    assert target_sub.field == SubmissionFields.TARGET
    assert target_sub.type == SubmissionTypes.UPLOAD
    assert target_sub.submitter == member
    assert target_sub.revision == unit.revision
    assert target_sub.creation_time == unit.change.submitted_on
    state_sub = new_subs[1]
    assert state_sub.old_value == "0"
    assert state_sub.new_value == "200"
    assert state_sub.field == SubmissionFields.STATE
    assert state_sub.type == SubmissionTypes.UPLOAD
    assert state_sub.submitter == member
    assert state_sub.revision == unit.revision
    assert state_sub.creation_time == unit.change.submitted_on


@pytest.mark.django_db
def test_update_upload_submission_type(store0):
    store0.state = PARSED
    unit = store0.units.first()
    last_sub_pk = unit.submission_set.order_by(
        "id").values_list("id", flat=True).last() or 0
    update_store(
        store0,
        [(unit.source, "%s UPDATED" % unit.source, False)],
        submission_type=SubmissionTypes.UPLOAD,
        store_revision=Revision.get() + 1)
    unit_source = store0.units[0].unit_source
    unit_change = store0.units[0].change
    assert unit_source.created_with == SubmissionTypes.SYSTEM
    assert unit_change.changed_with == SubmissionTypes.UPLOAD
    # there should be 2 new subs - state_change and target_change
    # and both should show as by UPLOAD
    new_subs = unit.submission_set.filter(id__gt=last_sub_pk)
    assert (
        list(new_subs.values_list("type", flat=True))
        == [SubmissionTypes.UPLOAD] * 2)


@pytest.mark.django_db
def test_update_upload_new_revision(store0, member):
    original_revision = store0.data.max_unit_revision
    old_unit = store0.units.first()
    update_store(
        store0,
        [("Hello, world", "Hello, world UPDATED", False)],
        submission_type=SubmissionTypes.UPLOAD,
        store_revision=Revision.get() + 1,
        user=member)
    old_unit.refresh_from_db()
    assert old_unit.state == OBSOLETE
    assert len(store0.units) == 1
    unit = store0.units[0]
    unit_source = unit.unit_source
    assert unit.revision > original_revision
    assert unit_source.created_by == member
    assert unit.change.submitted_by == member
    assert unit.creation_time == unit.change.submitted_on
    assert unit.change.reviewed_by is None
    assert unit.change.reviewed_on is None
    assert unit.target == "Hello, world UPDATED"
    assert unit.submission_set.count() == 0


@pytest.mark.django_db
def test_update_upload_again_new_revision(store0, member, member2):
    store = store0
    assert store.state == NEW
    original_unit = store0.units[0]
    update_store(
        store,
        [("Hello, world", "Hello, world UPDATED", False)],
        submission_type=SubmissionTypes.UPLOAD,
        store_revision=Revision.get() + 1,
        user=member)
    original_unit.refresh_from_db()
    assert original_unit.state == OBSOLETE
    store = Store.objects.get(pk=store0.pk)
    assert store.state == PARSED
    created_unit = store.units[0]
    assert created_unit.target == "Hello, world UPDATED"
    assert created_unit.state == TRANSLATED
    assert created_unit.submission_set.count() == 0
    old_unit_revision = store.data.max_unit_revision
    update_store(
        store0,
        [("Hello, world", "Hello, world UPDATED AGAIN", False)],
        submission_type=SubmissionTypes.WEB,
        user=member2,
        store_revision=Revision.get() + 1)
    assert created_unit.submission_set.count() == 1
    update_sub = created_unit.submission_set.first()
    store = Store.objects.get(pk=store0.pk)
    assert store.state == PARSED
    unit = store.units[0]
    unit_source = unit.unit_source
    assert unit.revision > old_unit_revision
    assert unit.target == "Hello, world UPDATED AGAIN"
    assert unit_source.created_by == member
    assert unit_source.created_with == SubmissionTypes.UPLOAD
    assert unit.change.submitted_by == member2
    assert unit.change.submitted_on >= unit.creation_time
    assert unit.change.reviewed_by is None
    assert unit.change.reviewed_on is None
    assert unit.change.changed_with == SubmissionTypes.WEB
    assert update_sub.creation_time == unit.change.submitted_on
    assert update_sub.type == unit.change.changed_with
    assert update_sub.field == SubmissionFields.TARGET
    assert update_sub.submitter == unit.change.submitted_by
    assert update_sub.old_value == created_unit.target
    assert update_sub.new_value == unit.target
    assert update_sub.revision == unit.revision


@pytest.mark.django_db
def test_update_upload_old_revision_unit_conflict(store0, admin, member):
    original_revision = Revision.get()
    original_unit = store0.units[0]
    update_store(
        store0,
        [("Hello, world", "Hello, world UPDATED", False)],
        submission_type=SubmissionTypes.UPLOAD,
        store_revision=original_revision + 1,
        user=admin)
    unit = store0.units[0]
    unit_source = unit.unit_source
    assert unit_source.created_by == admin
    updated_revision = unit.revision
    assert (
        unit_source.created_with
        == SubmissionTypes.UPLOAD)
    assert unit.change.submitted_by == admin
    assert (
        unit.change.changed_with
        == SubmissionTypes.UPLOAD)
    last_submit_time = unit.change.submitted_on
    assert last_submit_time >= unit.creation_time
    # load update with expired revision and conflicting unit
    unit = store0.units[0]
    unit.target = "Hello, world KEEP"
    unit.save()
    updated_revision = unit.revision
    subs_count = unit.submission_set.count()
    update_store(
        store0,
        [("Hello, world", "Hello, world CONFLICT", False)],
        submission_type=SubmissionTypes.WEB,
        store_revision=original_revision,
        user=member)
    assert subs_count == unit.submission_set.count()
    unit_source = unit.unit_source
    # unit target is not updated and revision is incremented
    # to force update to fs on next sync
    unit.refresh_from_db()
    assert store0.units[0].target == "Hello, world KEEP"
    assert unit.revision > updated_revision
    unit_source = original_unit.unit_source
    unit_source.created_by == admin
    assert unit_source.created_with == SubmissionTypes.SYSTEM
    unit.change.changed_with == SubmissionTypes.UPLOAD
    unit.change.submitted_by == admin
    unit.change.submitted_on == last_submit_time
    unit.change.reviewed_by is None
    unit.change.reviewed_on is None
    # but suggestion is added
    suggestion = store0.units[0].get_suggestions()[0]
    assert suggestion.target == "Hello, world CONFLICT"
    assert suggestion.user == member


@pytest.mark.django_db
def test_update_upload_new_revision_new_unit(store0, member):
    file_name = "pytest_pootle/data/po/tutorial/en/tutorial_update_new_unit.po"
    store0.state = PARSED
    old_unit_revision = store0.data.max_unit_revision
    _update_from_upload_file(
        store0,
        file_name,
        user=member,
        submission_type=SubmissionTypes.WEB)
    unit = store0.units.last()
    unit_source = unit.unit_source
    # the new unit has been added
    assert unit.submission_set.count() == 0
    assert unit.revision > old_unit_revision
    assert unit.target == 'Goodbye, world'
    assert unit_source.created_by == member
    assert unit_source.created_with == SubmissionTypes.WEB
    assert unit.change.submitted_by == member
    assert unit.change.changed_with == SubmissionTypes.WEB


@pytest.mark.django_db
def test_update_upload_old_revision_new_unit(store0, member2):
    store0.units.delete()
    store0.state = PARSED
    old_unit_revision = store0.data.max_unit_revision
    # load initial update
    _update_from_upload_file(
        store0,
        "pytest_pootle/data/po/tutorial/en/tutorial_update.po")
    # load old revision with new unit
    file_name = "pytest_pootle/data/po/tutorial/en/tutorial_update_old_unit.po"
    _update_from_upload_file(
        store0,
        file_name,
        user=member2,
        submission_type=SubmissionTypes.WEB)
    # the unit has been added because its not already obsoleted
    assert store0.units.count() == 2
    unit = store0.units.last()
    unit_source = unit.unit_source
    # the new unit has been added
    assert unit.submission_set.count() == 0
    assert unit.revision > old_unit_revision
    assert unit.target == 'Goodbye, world'
    assert unit_source.created_by == member2
    assert unit_source.created_with == SubmissionTypes.WEB
    assert unit.change.submitted_by == member2
    assert unit.change.changed_with == SubmissionTypes.WEB


def _test_store_update_indexes(store, *test_args):
    # make sure indexes are not fooed indexes only have to be unique
    indexes = [x.index for x in store.units]
    assert len(indexes) == len(set(indexes))


def _test_store_update_units_before(*test_args):
    # test what has happened to the units that were present before the update
    (store, units_update, store_revision, resolve_conflict,
     units_before, member_, member2) = test_args

    updates = {unit[0]: unit[1] for unit in units_update}

    from pootle.core.delegate import versioned
    vers = versioned.get(store.__class__)(store)
    old_store = vers.at_revision(store_revision or 0)

    for unit, change in units_before:
        updated_unit = store.unit_set.get(unitid=unit.unitid)

        if unit.source not in updates:
            # unit is not in update, target should be left unchanged
            assert updated_unit.target == unit.target
            assert updated_unit.change.submitted_by == change.submitted_by

            # depending on unit/store_revision should be obsoleted
            if unit.isobsolete() or store_revision >= unit.revision:
                assert updated_unit.isobsolete()
            else:
                assert not updated_unit.isobsolete()
        else:
            # unit is in update
            if store_revision >= unit.revision:
                assert not updated_unit.isobsolete()
            elif unit.isobsolete():
                # the unit has been obsoleted since store_revision
                assert updated_unit.isobsolete()
            else:
                assert not updated_unit.isobsolete()

            if not updated_unit.isobsolete():
                if store_revision >= unit.revision:
                    # file store wins outright
                    assert updated_unit.target == updates[unit.source]
                    if unit.target != updates[unit.source]:
                        # unit has changed, or was resurrected
                        assert updated_unit.change.submitted_by == member2

                        # damn mysql microsecond precision
                        if change.submitted_on.time().microsecond != 0:
                            assert (
                                updated_unit.change.submitted_on
                                != change.submitted_on)
                    elif unit.isobsolete():
                        # unit has changed, or was resurrected
                        assert updated_unit.change.reviewed_by == member2

                        # damn mysql microsecond precision
                        if change.reviewed_on.time().microsecond != 0:
                            assert (
                                updated_unit.change.reviewed_on
                                != change.reviewed_on)
                    else:
                        assert (
                            updated_unit.change.submitted_by
                            == change.submitted_by)
                        assert (
                            updated_unit.change.submitted_on
                            == change.submitted_on)
                    assert updated_unit.get_suggestions().count() == 0
                else:
                    # conflict found
                    old_unit = old_store.findid(unit.getid())
                    target_conflict = False
                    if not old_unit or old_unit.target != unit.target:
                        suggestion = updated_unit.get_suggestions()[0]
                        target_conflict = True
                    if target_conflict and resolve_conflict == POOTLE_WINS:
                        assert updated_unit.target == unit.target
                        assert (
                            updated_unit.change.submitted_by
                            == change.submitted_by)
                        assert suggestion.target == updates[unit.source]
                        assert suggestion.user == member2
                    elif target_conflict:
                        assert updated_unit.target == updates[unit.source]
                        assert updated_unit.change.submitted_by == member2
                        assert suggestion.target == unit.target
                        assert suggestion.user == change.submitted_by


def _test_store_update_ordering(*test_args):
    (store, units_update, store_revision, resolve_conflict_,
     units_before, member_, member2_) = test_args

    updates = {unit[0]: unit[1] for unit in units_update}
    old_units = {unit.source: unit for unit, change in units_before}

    # test ordering
    new_unit_list = []
    for unit, change_ in units_before:
        add_unit = (not unit.isobsolete()
                    and unit.source not in updates
                    and unit.revision > store_revision)
        if add_unit:
            new_unit_list.append(unit.source)
    for source, target_, is_fuzzy_ in units_update:
        if source in old_units:
            old_unit = old_units[source]
            should_add = (not old_unit.isobsolete()
                          or old_unit.revision <= store_revision)
            if should_add:
                new_unit_list.append(source)
        else:
            new_unit_list.append(source)
    assert new_unit_list == [x.source for x in store.units]


def _test_store_update_units_now(*test_args):
    (store, units_update, store_revision, resolve_conflict_,
     units_before, member_, member2_) = test_args

    # test that all the current units should be there
    updates = {unit[0]: unit[1] for unit in units_update}
    old_units = {unit.source: unit for unit, change in units_before}
    for unit in store.units:
        assert (
            unit.source in updates
            or (old_units[unit.source].revision > store_revision
                and not old_units[unit.source].isobsolete()))


@pytest.mark.django_db
def test_store_update(param_update_store_test):
    _test_store_update_indexes(*param_update_store_test)
    _test_store_update_units_before(*param_update_store_test)
    _test_store_update_units_now(*param_update_store_test)
    _test_store_update_ordering(*param_update_store_test)


@pytest.mark.django_db
def test_store_file_diff(store_diff_tests):
    diff, store, update_units, store_revision = store_diff_tests

    assert diff.target_store == store
    assert diff.source_revision == store_revision
    assert (
        update_units
        == [(x.source, x.target, x.isfuzzy())
            for x in diff.source_store.units[1:]]
        == [(v['source'], v['target'], v['state'] == 50)
            for v in diff.source_units.values()])
    assert diff.active_target_units == [x.source for x in store.units]
    assert diff.target_revision == store.get_max_unit_revision()
    assert (
        diff.target_units
        == {unit["source_f"]: unit
            for unit
            in store.unit_set.values("source_f", "index", "target_f",
                                     "state", "unitid", "id", "revision",
                                     "developer_comment", "translator_comment",
                                     "locations", "context")})
    diff_diff = diff.diff()
    if diff_diff is not None:
        assert (
            sorted(diff_diff.keys())
            == ["add", "index", "obsolete", "update"])

    # obsoleted units have no index - so just check they are all they match
    obsoleted = (store.unit_set.filter(state=OBSOLETE)
                               .filter(revision__gt=store_revision)
                               .values_list("source_f", flat=True))
    assert len(diff.obsoleted_target_units) == obsoleted.count()
    assert all(x in diff.obsoleted_target_units for x in obsoleted)

    assert (
        diff.updated_target_units
        == list(store.units.filter(revision__gt=store_revision)
                           .values_list("source_f", flat=True)))


@pytest.mark.django_db
def test_store_repr():
    store = Store.objects.first()
    assert str(store) == str(store.syncer.convert(store.syncer.file_class))
    assert repr(store) == u"<Store: %s>" % store.pootle_path


@pytest.mark.django_db
def test_store_po_deserializer(test_fs, store_po):

    with test_fs.open("data/po/complex.po") as test_file:
        test_string = test_file.read()
        ttk_po = getclass(test_file)(test_string)

    store_po.update(store_po.deserialize(test_string))
    assert len(ttk_po.units) - 1 == store_po.units.count()


@pytest.mark.django_db
def test_store_po_serializer(test_fs, store_po):

    with test_fs.open("data/po/complex.po") as test_file:
        test_string = test_file.read()
        ttk_po = getclass(test_file)(test_string)

    store_po.update(store_po.deserialize(test_string))
    store_io = io.BytesIO(store_po.serialize())
    store_ttk = getclass(store_io)(store_io.read())
    assert len(store_ttk.units) == len(ttk_po.units)


@pytest.mark.django_db
def test_store_po_serializer_custom(test_fs, store_po):

    class SerializerCheck(object):
        original_data = None
        context = None

    checker = SerializerCheck()

    class EGSerializer(Serializer):

        @property
        def output(self):
            checker.original_data = self.original_data
            checker.context = self.context

    @provider(serializers, sender=Project)
    def provide_serializers(**kwargs):
        return dict(eg_serializer=EGSerializer)

    with test_fs.open("data/po/complex.po") as test_file:
        test_string = test_file.read()
        # ttk_po = getclass(test_file)(test_string)
    store_po.update(store_po.deserialize(test_string))

    # add config to the project
    project = store_po.translation_project.project
    config.get(project.__class__, instance=project).set_config(
        "pootle.core.serializers",
        ["eg_serializer"])

    store_po.serialize()
    assert checker.context == store_po
    assert (
        not isinstance(checker.original_data, six.text_type)
        and isinstance(checker.original_data, str))
    assert checker.original_data == _store_as_string(store_po)


@pytest.mark.django_db
def test_store_po_deserializer_custom(test_fs, store_po):

    class DeserializerCheck(object):
        original_data = None
        context = None

    checker = DeserializerCheck()

    class EGDeserializer(Deserializer):

        @property
        def output(self):
            checker.context = self.context
            checker.original_data = self.original_data
            return self.original_data

    @provider(deserializers, sender=Project)
    def provide_deserializers(**kwargs):
        return dict(eg_deserializer=EGDeserializer)

    with test_fs.open("data/po/complex.po") as test_file:
        test_string = test_file.read()

    # add config to the project
    project = store_po.translation_project.project
    config.get().set_config(
        "pootle.core.deserializers",
        ["eg_deserializer"],
        project)
    store_po.deserialize(test_string)
    assert checker.original_data == test_string
    assert checker.context == store_po


@pytest.mark.django_db
def test_store_base_serializer(store_po):
    original_data = "SOME DATA"
    serializer = Serializer(store_po, original_data)
    assert serializer.context == store_po
    assert serializer.data == original_data


@pytest.mark.django_db
def test_store_base_deserializer(store_po):
    original_data = "SOME DATA"
    deserializer = Deserializer(store_po, original_data)
    assert deserializer.context == store_po
    assert deserializer.data == original_data


@pytest.mark.django_db
def test_store_set_bad_deserializers(store_po):
    project = store_po.translation_project.project
    with pytest.raises(ConfigurationError):
        config.get(project.__class__, instance=project).set_config(
            "pootle.core.deserializers",
            ["DESERIALIZER_DOES_NOT_EXIST"])

    class EGDeserializer(object):
        pass

    @provider(deserializers)
    def provide_deserializers(**kwargs):
        return dict(eg_deserializer=EGDeserializer)

    # must be list
    with pytest.raises(ConfigurationError):
        config.get(project.__class__, instance=project).set_config(
            "pootle.core.deserializers",
            "eg_deserializer")
    with pytest.raises(ConfigurationError):
        config.get(project.__class__, instance=project).set_config(
            "pootle.core.deserializers",
            dict(serializer="eg_deserializer"))

    config.get(project.__class__, instance=project).set_config(
        "pootle.core.deserializers",
        ["eg_deserializer"])


@pytest.mark.django_db
def test_store_set_bad_serializers(store_po):
    project = store_po.translation_project.project
    with pytest.raises(ConfigurationError):
        config.get(project.__class__, instance=project).set_config(
            "pootle.core.serializers",
            ["SERIALIZER_DOES_NOT_EXIST"])

    class EGSerializer(Serializer):
        pass

    @provider(serializers)
    def provide_serializers(**kwargs):
        return dict(eg_serializer=EGSerializer)

    # must be list
    with pytest.raises(ConfigurationError):
        config.get(project.__class__, instance=project).set_config(
            "pootle.core.serializers",
            "eg_serializer")
    with pytest.raises(ConfigurationError):
        config.get(project.__class__, instance=project).set_config(
            "pootle.core.serializers",
            dict(serializer="eg_serializer"))

    config.get(project.__class__, instance=project).set_config(
        "pootle.core.serializers",
        ["eg_serializer"])


@pytest.mark.django_db
def test_store_create_by_bad_path(project0):

    # bad project name
    with pytest.raises(Project.DoesNotExist):
        Store.objects.create_by_path(
            "/language0/does/not/exist.po")

    # bad language code
    with pytest.raises(Language.DoesNotExist):
        Store.objects.create_by_path(
            "/does/project0/not/exist.po")

    # project and project code dont match
    with pytest.raises(ValueError):
        Store.objects.create_by_path(
            "/language0/project1/store.po",
            project=project0)

    # bad store.ext
    with pytest.raises(ValueError):
        Store.objects.create_by_path(
            "/language0/project0/store_by_path.foo")

    # subdir doesnt exist
    path = '/language0/project0/path/to/subdir.po'
    with pytest.raises(Directory.DoesNotExist):
        Store.objects.create_by_path(
            path, create_directory=False)

    path = '/%s/project0/notp.po' % LanguageDBFactory().code
    with pytest.raises(TranslationProject.DoesNotExist):
        Store.objects.create_by_path(
            path, create_tp=False)


@pytest.mark.django_db
def test_store_create_by_path(po_directory):

    # create in tp
    path = '/language0/project0/path.po'
    store = Store.objects.create_by_path(path)
    assert store.pootle_path == path

    # "create" in tp again - get existing store
    store = Store.objects.create_by_path(path)
    assert store.pootle_path == path

    # create in existing subdir
    path = '/language0/project0/subdir0/exists.po'
    store = Store.objects.create_by_path(path)
    assert store.pootle_path == path

    # create in new subdir
    path = '/language0/project0/path/to/subdir.po'
    store = Store.objects.create_by_path(path)
    assert store.pootle_path == path


@pytest.mark.django_db
def test_store_create_by_path_with_project(project0):
    # create in tp with project
    path = '/language0/project0/path2.po'
    store = Store.objects.create_by_path(
        path, project=project0)
    assert store.pootle_path == path

    # create in existing subdir with project
    path = '/language0/project0/subdir0/exists2.po'
    store = Store.objects.create_by_path(
        path, project=project0)
    assert store.pootle_path == path

    # create in new subdir with project
    path = '/language0/project0/path/to/subdir2.po'
    store = Store.objects.create_by_path(
        path, project=project0)
    assert store.pootle_path == path


@pytest.mark.django_db
def test_store_create_by_new_tp_path(po_directory):
    language = LanguageDBFactory()
    path = '/%s/project0/tp.po' % language.code
    store = Store.objects.create_by_path(path)
    assert store.pootle_path == path
    assert store.translation_project.language == language

    language = LanguageDBFactory()
    path = '/%s/project0/with/subdir/tp.po' % language.code
    store = Store.objects.create_by_path(path)
    assert store.pootle_path == path
    assert store.translation_project.language == language


@pytest.mark.django_db
def test_store_create(tp0):
    tp = tp0
    project = tp.project
    registry = formats.get()
    po = Format.objects.get(name="po")
    po2 = registry.register("special_po_2", "po")
    po3 = registry.register("special_po_3", "po")
    xliff = Format.objects.get(name="xliff")
    project.filetypes.add(xliff)
    project.filetypes.add(po2)
    project.filetypes.add(po3)

    store = Store.objects.create(
        name="store.po",
        parent=tp.directory,
        translation_project=tp)
    assert store.filetype == po
    assert not store.is_template
    store = Store.objects.create(
        name="store.pot",
        parent=tp.directory,
        translation_project=tp)
    # not in source_language folder
    assert not store.is_template
    assert store.filetype == po
    store = Store.objects.create(
        name="store.xliff",
        parent=tp.directory,
        translation_project=tp)
    assert store.filetype == xliff

    # push po to the back of the queue
    project.filetypes.remove(po)
    project.filetypes.add(po)
    store = Store.objects.create(
        name="another_store.po",
        parent=tp.directory,
        translation_project=tp)
    assert store.filetype == po2
    store = Store.objects.create(
        name="another_store.pot",
        parent=tp.directory,
        translation_project=tp)
    assert store.filetype == po
    store = Store.objects.create(
        name="another_store.xliff",
        parent=tp.directory,
        translation_project=tp)

    with pytest.raises(UnrecognizedFiletype):
        store = Store.objects.create(
            name="another_store.foo",
            parent=tp.directory,
            translation_project=tp)


@pytest.mark.django_db
def test_store_create_name_with_slashes_or_backslashes(tp0):
    """Test Stores are not created with (back)slashes on their name."""

    with pytest.raises(ValidationError):
        Store.objects.create(name="slashed/name.po", parent=tp0.directory,
                             translation_project=tp0)

    with pytest.raises(ValidationError):
        Store.objects.create(name="backslashed\\name.po", parent=tp0.directory,
                             translation_project=tp0)


@pytest.mark.django_db
def test_store_get_file_class():
    store = Store.objects.filter(
        translation_project__project__code="project0",
        translation_project__language__code="language0").first()

    # this matches because po is recognised by ttk
    assert store.syncer.file_class == getclass(store)

    # file_class is cached so lets delete it
    del store.syncer.__dict__["file_class"]

    class CustomFormatClass(object):
        pass

    @provider(format_classes)
    def format_class_provider(**kwargs):
        return dict(po=CustomFormatClass)

    # we get the CutomFormatClass as it was registered
    assert store.syncer.file_class is CustomFormatClass

    # the Store.filetype is used in this case not the name
    store.name = "new_store_name.foo"
    del store.syncer.__dict__["file_class"]
    assert store.syncer.file_class is CustomFormatClass

    # lets register a foo filetype
    format_registry = formats.get()
    foo_filetype = format_registry.register("foo", "foo")

    store.filetype = foo_filetype
    store.save()

    # oh no! not recognised by ttk
    del store.syncer.__dict__["file_class"]
    with pytest.raises(ValueError):
        store.syncer.file_class

    @provider(format_classes)
    def another_format_class_provider(**kwargs):
        return dict(foo=CustomFormatClass)

    # works now
    assert store.syncer.file_class is CustomFormatClass

    format_classes.disconnect(format_class_provider)
    format_classes.disconnect(another_format_class_provider)


@pytest.mark.django_db
def test_store_get_template_file_class(po_directory, templates):
    project = ProjectDBFactory(source_language=templates)
    tp = TranslationProjectFactory(language=templates, project=project)
    format_registry = formats.get()
    foo_filetype = format_registry.register("foo", "foo", template_extension="bar")
    tp.project.filetypes.add(foo_filetype)
    store = Store.objects.create(
        name="mystore.bar",
        translation_project=tp,
        parent=tp.directory)

    # oh no! not recognised by ttk
    with pytest.raises(ValueError):
        store.syncer.file_class

    class CustomFormatClass(object):
        pass

    @provider(format_classes)
    def format_class_provider(**kwargs):
        return dict(foo=CustomFormatClass)

    assert store.syncer.file_class == CustomFormatClass

    format_classes.disconnect(format_class_provider)


@pytest.mark.django_db
def test_store_create_templates(po_directory, templates):
    project = ProjectDBFactory(source_language=templates)
    tp = TranslationProjectFactory(language=templates, project=project)
    po = Format.objects.get(name="po")
    store = Store.objects.create(
        name="mystore.pot",
        translation_project=tp,
        parent=tp.directory)
    assert store.filetype == po
    assert store.is_template


@pytest.mark.django_db
def test_store_get_or_create_templates(po_directory, templates):
    project = ProjectDBFactory(source_language=templates)
    tp = TranslationProjectFactory(language=templates, project=project)
    po = Format.objects.get(name="po")
    store = Store.objects.get_or_create(
        name="mystore.pot",
        translation_project=tp,
        parent=tp.directory)[0]
    assert store.filetype == po
    assert store.is_template


@pytest.mark.django_db
def test_store_diff(diffable_stores):
    target_store, source_store = diffable_stores
    differ = StoreDiff(
        target_store,
        source_store,
        target_store.get_max_unit_revision() + 1)
    # no changes
    assert not differ.diff()
    assert differ.target_store == target_store
    assert differ.source_store == source_store


@pytest.mark.django_db
def test_store_diff_delete_target_unit(diffable_stores):
    target_store, source_store = diffable_stores

    # delete a unit in the target store
    remove_unit = target_store.units.first()
    remove_unit.delete()

    # the unit will always be re-added (as its not obsolete)
    # with source_revision to the max
    differ = StoreDiff(
        target_store,
        source_store,
        target_store.get_max_unit_revision())
    result = differ.diff()
    assert result["add"][0][0].source_f == remove_unit.source_f
    assert len(result["add"]) == 1
    assert len(result["index"]) == 0
    assert len(result["obsolete"]) == 0
    assert result['update'] == (set(), {})

    # and source_revision to 0
    differ = StoreDiff(
        target_store,
        source_store,
        0)
    result = differ.diff()
    assert result["add"][0][0].source_f == remove_unit.source_f
    assert len(result["add"]) == 1
    assert len(result["index"]) == 0
    assert len(result["obsolete"]) == 0
    assert result['update'] == (set(), {})


@pytest.mark.django_db
def test_store_diff_delete_source_unit(diffable_stores):
    target_store, source_store = diffable_stores

    # delete a unit in the source store
    remove_unit = source_store.units.first()
    remove_unit.delete()

    # set the source_revision to max and the unit will be obsoleted
    differ = StoreDiff(
        target_store,
        source_store,
        target_store.get_max_unit_revision())
    result = differ.diff()
    to_remove = target_store.units.get(unitid=remove_unit.unitid)
    assert result["obsolete"] == [to_remove.pk]
    assert len(result["obsolete"]) == 1
    assert len(result["add"]) == 0
    assert len(result["index"]) == 0


@pytest.mark.django_db
def test_store_diff_delete_obsoleted_target_unit(diffable_stores):
    target_store, source_store = diffable_stores
    # delete a unit in the source store
    remove_unit = source_store.units.first()
    remove_unit.delete()
    # and obsolete the same unit in the target
    obsolete_unit = target_store.units.get(unitid=remove_unit.unitid)
    obsolete_unit.makeobsolete()
    obsolete_unit.save()
    # as the unit is already obsolete - nothing
    differ = StoreDiff(
        target_store,
        source_store,
        target_store.get_max_unit_revision() + 1)
    assert not differ.diff()


@pytest.mark.django_db
def test_store_diff_obsoleted_target_unit(diffable_stores):
    target_store, source_store = diffable_stores
    # obsolete a unit in target
    obsolete_unit = target_store.units.first()
    obsolete_unit.makeobsolete()
    obsolete_unit.save()
    # as the revision is higher it gets unobsoleted
    differ = StoreDiff(
        target_store,
        source_store,
        target_store.get_max_unit_revision() + 1)
    result = differ.diff()
    assert result["update"][0] == set([obsolete_unit.pk])
    assert len(result["update"][1]) == 1
    assert result["update"][1][obsolete_unit.unitid]["dbid"] == obsolete_unit.pk

    # if the revision is less - no change
    differ = StoreDiff(
        target_store,
        source_store,
        target_store.get_max_unit_revision() - 1)
    assert not differ.diff()


@pytest.mark.django_db
def test_store_diff_update_target_unit(diffable_stores):
    target_store, source_store = diffable_stores
    # update a unit in target
    update_unit = target_store.units.first()
    update_unit.target_f = "Some other string"
    update_unit.save()

    # the unit is always marked for update
    differ = StoreDiff(
        target_store,
        source_store,
        target_store.get_max_unit_revision() + 1)
    result = differ.diff()
    assert result["update"][0] == set([update_unit.pk])
    assert result["update"][1] == {}
    assert len(result["add"]) == 0
    assert len(result["index"]) == 0

    differ = StoreDiff(
        target_store,
        source_store,
        0)
    result = differ.diff()
    assert result["update"][0] == set([update_unit.pk])
    assert result["update"][1] == {}
    assert len(result["add"]) == 0
    assert len(result["index"]) == 0


@pytest.mark.django_db
def test_store_diff_update_source_unit(diffable_stores):
    target_store, source_store = diffable_stores
    # update a unit in source
    update_unit = source_store.units.first()
    update_unit.target_f = "Some other string"
    update_unit.save()

    target_unit = target_store.units.get(
        unitid=update_unit.unitid)

    # the unit is always marked for update
    differ = StoreDiff(
        target_store,
        source_store,
        target_store.get_max_unit_revision() + 1)
    result = differ.diff()
    assert result["update"][0] == set([target_unit.pk])
    assert result["update"][1] == {}
    assert len(result["add"]) == 0
    assert len(result["index"]) == 0
    differ = StoreDiff(
        target_store,
        source_store,
        0)
    result = differ.diff()
    assert result["update"][0] == set([target_unit.pk])
    assert result["update"][1] == {}
    assert len(result["add"]) == 0
    assert len(result["index"]) == 0


@pytest.mark.django_db
def test_store_diff_custom(diffable_stores):
    target_store, source_store = diffable_stores

    class CustomDiffableStore(DiffableStore):
        pass

    @provider(format_diffs)
    def format_diff_provider(**kwargs):
        return {
            target_store.filetype.name: CustomDiffableStore}

    differ = StoreDiff(
        target_store,
        source_store,
        target_store.get_max_unit_revision() + 1)

    assert isinstance(
        differ.diffable, CustomDiffableStore)


@pytest.mark.django_db
def test_store_diff_delete_obsoleted_source_unit(diffable_stores):
    target_store, source_store = diffable_stores
    # delete a unit in the target store
    remove_unit = target_store.units.first()
    remove_unit.delete()
    # and obsolete the same unit in the target
    obsolete_unit = source_store.units.get(unitid=remove_unit.unitid)
    obsolete_unit.makeobsolete()
    obsolete_unit.save()
    # as the unit is already obsolete - nothing
    differ = StoreDiff(
        target_store,
        source_store,
        target_store.get_max_unit_revision() + 1)
    assert not differ.diff()


@pytest.mark.django_db
def test_store_syncer(tp0):
    store = tp0.stores.live().first()
    assert isinstance(store.syncer, PoStoreSyncer)
    assert store.syncer.file_class == getclass(store)
    assert store.syncer.translation_project == store.translation_project
    assert (
        store.syncer.language
        == store.translation_project.language)
    assert (
        store.syncer.project
        == store.translation_project.project)
    assert (
        store.syncer.source_language
        == store.translation_project.project.source_language)


@pytest.mark.django_db
def test_store_syncer_obsolete_unit(tp0):
    store = tp0.stores.live().first()
    unit = store.units.filter(state=TRANSLATED).first()
    unit_syncer = store.syncer.unit_sync_class(unit)
    newunit = unit_syncer.create_unit(store.syncer.file_class.UnitClass)

    # unit is untranslated, its always just deleted
    obsolete, deleted = store.syncer.obsolete_unit(newunit, True)
    assert not obsolete
    assert deleted
    obsolete, deleted = store.syncer.obsolete_unit(newunit, False)
    assert not obsolete
    assert deleted

    # set unit to translated
    newunit.target = unit.target

    # if conservative, nothings changed
    obsolete, deleted = store.syncer.obsolete_unit(newunit, True)
    assert not obsolete
    assert not deleted

    # not conservative and the unit is deleted
    obsolete, deleted = store.syncer.obsolete_unit(newunit, False)
    assert obsolete
    assert not deleted


@pytest.mark.django_db
def test_store_syncer_sync_store(tp0, dummy_store_syncer):
    store = tp0.stores.live().first()
    DummyStoreSyncer, __, expected = dummy_store_syncer
    disk_store = store.syncer.convert()
    dummy_syncer = DummyStoreSyncer(store, expected=expected)
    result = dummy_syncer.sync(
        disk_store,
        expected["last_revision"],
        update_structure=expected["update_structure"],
        conservative=expected["conservative"])
    assert result[0] is True
    assert result[1]["updated"] == expected["changes"]
    # conservative makes no diff here
    expected["conservative"] = False
    dummy_syncer = DummyStoreSyncer(store, expected=expected)
    result = dummy_syncer.sync(
        disk_store,
        expected["last_revision"],
        update_structure=expected["update_structure"],
        conservative=expected["conservative"])
    assert result[0] is True
    assert result[1]["updated"] == expected["changes"]


@pytest.mark.django_db
def test_store_syncer_sync_store_no_changes(tp0, dummy_store_syncer):
    store = tp0.stores.live().first()
    DummyStoreSyncer, __, expected = dummy_store_syncer
    disk_store = store.syncer.convert()
    dummy_syncer = DummyStoreSyncer(store, expected=expected)

    # no changes
    expected["changes"] = []
    expected["conservative"] = True
    dummy_syncer = DummyStoreSyncer(store, expected=expected)
    result = dummy_syncer.sync(
        disk_store,
        expected["last_revision"],
        expected["update_structure"],
        expected["conservative"])
    assert result[0] is False
    assert not result[1].get("updated")

    # conservative makes no diff here
    expected["conservative"] = False
    dummy_syncer = DummyStoreSyncer(store, expected=expected)
    result = dummy_syncer.sync(
        disk_store,
        expected["last_revision"],
        expected["update_structure"],
        expected["conservative"])
    assert result[0] is False
    assert not result[1].get("updated")


@pytest.mark.django_db
def test_store_syncer_sync_store_structure(tp0, dummy_store_syncer):
    store = tp0.stores.live().first()
    DummyStoreSyncer, DummyDiskStore, expected = dummy_store_syncer

    disk_store = DummyDiskStore(expected)
    expected["update_structure"] = True
    expected["changes"] = []
    dummy_syncer = DummyStoreSyncer(store, expected=expected)
    result = dummy_syncer.sync(
        disk_store,
        expected["last_revision"],
        expected["update_structure"],
        expected["conservative"])
    assert result[0] is True
    assert result[1]["updated"] == []
    assert result[1]["obsolete"] == 8
    assert result[1]["deleted"] == 9
    assert result[1]["added"] == 10

    expected["obsolete_units"] = []
    expected["new_units"] = []
    expected["changes"] = []
    dummy_syncer = DummyStoreSyncer(store, expected=expected)
    result = dummy_syncer.sync(
        disk_store,
        expected["last_revision"],
        expected["update_structure"],
        expected["conservative"])
    assert result[0] is False


@pytest.mark.django_db
def test_store_syncer_sync_update_structure(dummy_store_structure_syncer, tp0):
    store = tp0.stores.live().first()
    DummyStoreSyncer, DummyDiskStore, DummyUnit = dummy_store_structure_syncer
    expected = dict(
        unit_class="FOO",
        conservative=True,
        obsolete_delete=(True, True),
        obsolete_units=["a", "b", "c"])
    expected["new_units"] = [
        DummyUnit(unit, expected=expected)
        for unit in ["5", "6", "7"]]
    syncer = DummyStoreSyncer(store, expected=expected)
    disk_store = DummyDiskStore(expected)
    result = syncer.update_structure(
        disk_store,
        expected["obsolete_units"],
        expected["new_units"],
        expected["conservative"])
    obsolete_units = (
        len(expected["obsolete_units"])
        if expected["obsolete_delete"][0]
        else 0)
    deleted_units = (
        len(expected["obsolete_units"])
        if expected["obsolete_delete"][1]
        else 0)
    new_units = len(expected["new_units"])
    assert result == (obsolete_units, deleted_units, new_units)


def _test_get_new(results, syncer, old_ids, new_ids):
    assert list(results) == list(
        syncer.store.findid_bulk(
            [syncer.dbid_index.get(uid)
             for uid
             in new_ids - old_ids]))


def _test_get_obsolete(results, disk_store, syncer, old_ids, new_ids):
    assert list(results) == list(
        disk_store.findid(uid)
        for uid
        in old_ids - new_ids
        if (disk_store.findid(uid)
            and not disk_store.findid(uid).isobsolete()))


@pytest.mark.django_db
def test_store_syncer_obsolete_units(dummy_store_syncer_units, tp0):
    store = tp0.stores.live().first()
    disk_store = store.syncer.convert()
    expected = dict(
        old_ids=set(),
        new_ids=set(),
        disk_ids={})
    syncer = dummy_store_syncer_units(store, expected=expected)
    results = syncer.get_units_to_obsolete(
        disk_store, expected["old_ids"], expected["new_ids"])
    _test_get_obsolete(
        results, disk_store, syncer,
        expected["old_ids"], expected["new_ids"])
    expected = dict(
        old_ids=set(["2", "3", "4"]),
        new_ids=set(["3", "4", "5"]),
        disk_ids={"3": "foo", "4": "bar", "5": "baz"})
    results = syncer.get_units_to_obsolete(
        disk_store, expected["old_ids"], expected["new_ids"])
    _test_get_obsolete(
        results, disk_store, syncer, expected["old_ids"], expected["new_ids"])


@pytest.mark.django_db
def test_store_syncer_new_units(dummy_store_syncer_units, tp0):
    store = tp0.stores.live().first()
    expected = dict(
        old_ids=set(),
        new_ids=set(),
        disk_ids={},
        db_ids={})
    syncer = dummy_store_syncer_units(store, expected=expected)
    results = syncer.get_new_units(
        expected["old_ids"], expected["new_ids"])
    _test_get_new(
        results, syncer, expected["old_ids"], expected["new_ids"])
    expected = dict(
        old_ids=set(["2", "3", "4"]),
        new_ids=set(["3", "4", "5"]),
        db_ids={"3": "foo", "4": "bar", "5": "baz"})
    syncer = dummy_store_syncer_units(store, expected=expected)
    results = syncer.get_new_units(
        expected["old_ids"], expected["new_ids"])
    _test_get_new(
        results, syncer, expected["old_ids"], expected["new_ids"])


@pytest.mark.django_db
def test_store_path(store0):
    assert store0.path == to_tp_relative_path(store0.pootle_path)


@pytest.mark.django_db
def test_store_sync_empty(project0_nongnu, tp0, caplog, settings):
    store = StoreDBFactory(
        name="empty.po",
        translation_project=tp0,
        parent=tp0.directory)
    file_path = _sync_store(settings, store)
    assert os.path.exists(file_path)
    modified = os.stat(file_path).st_mtime
    file_path = _sync_store(settings, store)
    assert modified == os.stat(file_path).st_mtime
    # warning message - nothing changes
    file_path = _sync_store(settings, store)
    assert modified == os.stat(file_path).st_mtime


@pytest.mark.django_db
def test_store_sync_template(project0_nongnu, templates_project0, caplog, settings):
    template = templates_project0.stores.first()
    file_path = _sync_store(settings, template, force_add=True)
    modified = os.stat(file_path).st_mtime
    unit = template.units.first()
    unit.target = "NEW TARGET"
    unit.save()
    _sync_store(settings, template)
    assert modified <= os.stat(file_path).st_mtime


@pytest.mark.django_db
def test_store_update_with_state_change(store0, admin):
    units = dict([(x.id, (x.source, x.target, not x.isfuzzy()))
                  for x in store0.units])

    update_store(
        store0,
        units=units.values(),
        store_revision=store0.data.max_unit_revision,
        user=admin)

    for unit_id, unit in units.items():
        assert unit[2] == store0.units.get(id=unit_id).isfuzzy()


@pytest.mark.django_db
def test_roundtrip_xliff(store_po, test_fs, xliff):
    project = store_po.translation_project.project
    filetype_tool = project.filetype_tool
    project.filetypes.add(xliff)
    filetype_tool.set_store_filetype(store_po, xliff)
    with test_fs.open(['data', 'xliff', 'manyfiles.xliff']) as f:
        file_store = getclass(f)(f.read())
    store_po.update(file_store)
    serialized = store_po.deserialize(store_po.serialize())
    assert serialized.units[0].getid() == u'file0\x04hello'
    assert serialized.units[1].getid() == u'file1\x04world'


@pytest.mark.django_db
def test_update_xliff(store_po, test_fs, xliff):
    project = store_po.translation_project.project
    filetype_tool = project.filetype_tool
    project.filetypes.add(xliff)
    filetype_tool.set_store_filetype(store_po, xliff)

    with test_fs.open(['data', 'xliff', 'welcome.xliff']) as f:
        file_store = getclass(f)(f.read())
    store_po.update(file_store)
    unit = store_po.units[0]
    assert unit.istranslated()

    with test_fs.open(['data', 'xliff', 'updated_welcome.xliff']) as f:
        file_store = getclass(f)(f.read())
    store_po.update(file_store)
    updated_unit = store_po.units.get(id=unit.id)
    assert unit.source != updated_unit.source


@pytest.mark.django_db
def test_update_resurrect(store_po, test_fs):
    with test_fs.open(['data', 'po', 'obsolete.po']) as f:
        file_store = getclass(f)(f.read())
    store_po.update(file_store)
    obsolete_units = store_po.unit_set.filter(state=OBSOLETE)
    obsolete_ids = list(obsolete_units.values_list('id', flat=True))
    assert len(obsolete_ids) > 0

    with test_fs.open(['data', 'po', 'resurrected.po']) as f:
        file_store = getclass(f)(f.read())

    store_revision = store_po.data.max_unit_revision
    # set store_revision as we do in update_stores cli command
    store_po.update(file_store, store_revision=store_revision - 1)
    obsolete_units = store_po.unit_set.filter(state=OBSOLETE)
    assert obsolete_units.count() == len(obsolete_ids)
    for unit in obsolete_units.filter(id__in=obsolete_ids):
        assert unit.isobsolete()

    # set store_revision as we do in update_stores cli command
    store_po.update(file_store, store_revision=store_revision)
    units = store_po.units.filter(id__in=obsolete_ids)
    assert units.count() == len(obsolete_ids)
    for unit in units:
        assert not unit.isobsolete()


@pytest.mark.django_db
def test_store_comment_update(store0, member):
    ttk = store0.deserialize(store0.serialize())
    fileunit = ttk.units[-1]
    fileunit.removenotes()
    fileunit.addnote("A new comment")
    unit = store0.findid(fileunit.getid())
    last_sub_pk = unit.submission_set.order_by(
        "id").values_list("id", flat=True).last() or 0
    store0.update(
        ttk, store_revision=store0.data.max_unit_revision + 1,
        user=member
    )
    assert ttk.units[-1].getnotes("translator") == "A new comment"
    unit = store0.units.get(id=unit.id)
    assert unit.translator_comment == "A new comment"
    assert unit.change.commented_by == member
    new_subs = unit.submission_set.filter(id__gt=last_sub_pk).order_by("id")
    assert new_subs.count() == 1
    comment_sub = new_subs[0]
    assert comment_sub.old_value == ""
    assert comment_sub.new_value == "A new comment"
    assert comment_sub.field == SubmissionFields.COMMENT
    assert comment_sub.type == SubmissionTypes.SYSTEM
    assert comment_sub.submitter == member
    assert comment_sub.revision == unit.revision
    assert comment_sub.creation_time == unit.change.commented_on

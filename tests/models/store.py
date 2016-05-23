# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import io
import os
import shutil
import time

import six

import pytest

from pytest_pootle.factories import LanguageDBFactory
from pytest_pootle.utils import update_store

from translate.storage.factory import getclass

from django.core.files.uploadedfile import SimpleUploadedFile

from pootle.core.delegate import config
from pootle.core.models import Revision
from pootle.core.delegate import deserializers, serializers
from pootle.core.plugin import provider
from pootle.core.serializers import Serializer, Deserializer
from pootle_app.models import Directory
from pootle_config.exceptions import ConfigurationError
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_statistics.models import SubmissionTypes
from pootle_store.models import NEW, OBSOLETE, PARSED, POOTLE_WINS, Store
from pootle_store.util import parse_pootle_revision
from pootle_translationproject.models import TranslationProject

from .unit import _update_translation


def _update_from_upload_file(store, update_file,
                             content_type="text/x-gettext-translation",
                             user=None, submission_type=None):
    with open(update_file, "r") as f:
        upload = SimpleUploadedFile(os.path.basename(update_file),
                                    f.read(),
                                    content_type)
    if store.state < PARSED:
        store.update(store.file.store)
    test_store = getclass(upload)(upload.read())
    store_revision = parse_pootle_revision(test_store)
    store.update(test_store, store_revision=store_revision,
                 user=user, submission_type=submission_type)


def _store_as_string(store):
    ttk = store.convert(store.get_file_class())
    if hasattr(ttk, "updateheader"):
        # FIXME We need those headers on import
        # However some formats just don't support setting metadata
        ttk.updateheader(
            add=True, X_Pootle_Path=store.pootle_path)
        ttk.updateheader(
            add=True, X_Pootle_Revision=store.get_max_unit_revision())
    return str(ttk)


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
        store.update(store.file.store)

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
        store.update(store.file.store)

    assert fr_tutorial_remove_sync_po.file.exists()
    os.remove(fr_tutorial_remove_sync_po.file.path)

    from pootle_store.models import Store
    store = Store.objects.get(pootle_path=pootle_path)
    assert not store.file.exists()
    store.sync()
    assert store.file.exists()


@pytest.mark.django_db
def test_update_from_ts(en_tutorial_po, test_fs):
    # Parse store
    en_tutorial_po.update_from_disk()
    tp = en_tutorial_po.translation_project
    with test_fs.open(['data', 'ts', tp.real_path, 'tutorial.ts']) as f:
        store = getclass(f)(f.read())
    en_tutorial_po.update(store)

    assert(not en_tutorial_po.units[1].hasplural())
    assert(en_tutorial_po.units[2].hasplural())


@pytest.mark.django_db
def test_update_ts_plurals(store_po, test_fs):
    with test_fs.open(['data', 'ts', 'add_plurals.ts']) as f:
        file_store = getclass(f)(f.read())
    store_po.update(file_store)
    assert store_po.units[0].hasplural()

    with test_fs.open(['data', 'ts', 'update_plurals.ts']) as f:
        file_store = getclass(f)(f.read())
    store_po.update(file_store)
    assert store_po.units[0].hasplural()


@pytest.mark.django_db
def test_update_with_non_ascii(en_tutorial_po, test_fs):
    # Parse store
    en_tutorial_po.update_from_disk()
    tp = en_tutorial_po.translation_project
    with test_fs.open(['data', 'po', tp.real_path,
                       'tutorial_non_ascii.po']) as f:
        store = getclass(f)(f.read())
    en_tutorial_po.update(store)
    assert en_tutorial_po.units[0].target == "Hèllö, wôrld"


@pytest.mark.django_db
def test_update_unit_order(ru_tutorial_po):
    """Tests unit order after a specific update.
    """

    # Parse stores
    ru_tutorial_po.update(ru_tutorial_po.file.store)

    # Set last sync revision
    ru_tutorial_po.sync()

    assert ru_tutorial_po.file.exists()

    old_unit_list = ['1->2', '2->4', '3->3', '4->5']
    updated_unit_list = list(
        [unit.unitid for unit in ru_tutorial_po.units]
    )
    assert old_unit_list == updated_unit_list

    # as the tutorial_updated.po file has no revision header we need to set it
    # manually for this test to pass
    ru_tutorial_po.file = 'tutorial/ru/tutorial_updated.po'

    current_revision = ru_tutorial_po.get_max_unit_revision()
    ru_tutorial_po.update(ru_tutorial_po.file.store,
                          store_revision=current_revision)

    old_unit_list = [
        'X->1', '1->2', '3->3', '2->4',
        '4->5', 'X->6', 'X->7', 'X->8']
    updated_unit_list = list(
        [unit.unitid for unit in ru_tutorial_po.units]
    )
    assert old_unit_list == updated_unit_list


@pytest.mark.django_db
def test_update_save_changed_units(ru_update_save_changed_units_po):
    """Tests that any update saves changed units only.
    """
    store = ru_update_save_changed_units_po

    store.update(store.file.store)
    unit_list = list(store.units)
    # Set last sync revision
    store.sync()

    # delay for 1 sec, we'll compare mtimes
    time.sleep(1)
    store.file = 'tutorial/ru/update_save_changed_units_updated.po'
    store.update(store.file.store)
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

    # Store is already parsed and store.last_sync_revision should be equal to
    # max unit revision
    assert store.last_sync_revision == store.get_max_unit_revision()

    # store.last_sync_revision is not changed after empty update
    saved_last_sync_revision = store.last_sync_revision
    store.update_from_disk()
    assert store.last_sync_revision == saved_last_sync_revision

    dir_path = os.path.join(store.translation_project.project.get_real_path(),
                            store.translation_project.language.code)
    copied_initial_filepath = os.path.join(
        dir_path,
        'update_set_last_sync_revision.po.temp'
    )
    shutil.copy(store.file.path, copied_initial_filepath)
    updated_filepath = os.path.join(
        dir_path,
        'update_set_last_sync_revision_updated.po'
    )
    shutil.copy(updated_filepath, store.file.path)

    # any non-empty update sets last_sync_revision to next global revision
    next_revision = Revision.get() + 1
    store.update_from_disk()
    assert store.last_sync_revision == next_revision

    # store.last_sync_revision is not changed after empty update (even if it
    # has unsynced units)
    item_index = 0
    next_unit_revision = Revision.get() + 1
    dbunit = _update_translation(store, item_index, {'target': u'first'},
                                 sync=False)
    assert dbunit.revision == next_unit_revision
    store.update_from_disk()
    assert store.last_sync_revision == next_revision

    # Non-empty update sets store.last_sync_revision to next global revision
    # (even the store has unsynced units).  There is only one unsynced unit in
    # this case so its revision should be set next to store.last_sync_revision
    next_revision = Revision.get() + 1
    shutil.move(copied_initial_filepath, store.file.path)
    store.update_from_disk()
    assert store.last_sync_revision == next_revision
    # Get unsynced unit in DB. Its revision should be greater
    # than store.last_sync_revision to allow to keep this change during
    # update from a file
    dbunit = store.getitem(item_index)
    assert dbunit.revision == store.last_sync_revision + 1


@pytest.mark.django_db
def test_update_upload_defaults(en_tutorial_po, system):
    update_store(
        en_tutorial_po,
        [("Hello, world", "Hello, world UPDATED")],
        user=system,
        store_revision=Revision.get() + 1)
    assert en_tutorial_po.units[0].submitted_by == system
    assert (en_tutorial_po.units[0].submission_set.first().type
            == SubmissionTypes.SYSTEM)


@pytest.mark.django_db
def test_update_upload_member_user(en_tutorial_po, member):
    update_store(
        en_tutorial_po,
        [("Hello, world", "Hello, world UPDATED")],
        user=member,
        store_revision=Revision.get() + 1)
    assert en_tutorial_po.units[0].submitted_by == member


@pytest.mark.django_db
def test_update_upload_submission_type(en_tutorial_po):
    update_store(
        en_tutorial_po,
        [("Hello, world", "Hello, world UPDATED")],
        submission_type=SubmissionTypes.UPLOAD,
        store_revision=Revision.get() + 1)
    assert (en_tutorial_po.units[0].submission_set.first().type
            == SubmissionTypes.UPLOAD)


@pytest.mark.django_db
def test_update_upload_new_revision(en_tutorial_po):
    update_store(
        en_tutorial_po,
        [("Hello, world", "Hello, world UPDATED")],
        submission_type=SubmissionTypes.UPLOAD,
        store_revision=Revision.get() + 1)
    assert en_tutorial_po.units[0].target == "Hello, world UPDATED"


@pytest.mark.django_db
def test_update_upload_again_new_revision(en_tutorial_po_no_file):
    store = en_tutorial_po_no_file
    assert store.state == NEW
    update_store(
        store,
        [("Hello, world", "Hello, world UPDATED")],
        submission_type=SubmissionTypes.UPLOAD,
        store_revision=Revision.get() + 1)
    store = Store.objects.get(pk=store.pk)
    assert store.state == PARSED
    assert store.units[0].target == "Hello, world UPDATED"

    update_store(
        store,
        [("Hello, world", "Hello, world UPDATED AGAIN")],
        submission_type=SubmissionTypes.UPLOAD,
        store_revision=Revision.get() + 1)
    store = Store.objects.get(pk=store.pk)
    assert store.state == PARSED
    assert store.units[0].target == "Hello, world UPDATED AGAIN"


@pytest.mark.django_db
def test_update_upload_old_revision_unit_conflict(en_tutorial_po):
    original_revision = Revision.get()
    update_store(
        en_tutorial_po,
        [("Hello, world", "Hello, world UPDATED")],
        submission_type=SubmissionTypes.UPLOAD,
        store_revision=original_revision + 1)

    # load update with expired revision and conflicting unit
    update_store(
        en_tutorial_po,
        [("Hello, world", "Hello, world CONFLICT")],
        submission_type=SubmissionTypes.UPLOAD,
        store_revision=original_revision)

    # unit target is not updated
    assert en_tutorial_po.units[0].target == "Hello, world UPDATED"

    # but suggestion is added
    suggestion = en_tutorial_po.units[0].get_suggestions()[0].target
    assert suggestion == "Hello, world CONFLICT"


@pytest.mark.django_db
def test_update_upload_new_revision_new_unit(en_tutorial_po):
    file_name = "pytest_pootle/data/po/tutorial/en/tutorial_update_new_unit.po"
    _update_from_upload_file(en_tutorial_po, file_name)

    # the new unit has been added
    assert en_tutorial_po.units[1].target == 'Goodbye, world'


@pytest.mark.django_db
def test_update_upload_old_revision_new_unit(en_tutorial_po):

    # load initial update
    _update_from_upload_file(en_tutorial_po,
                             "pytest_pootle/data/po/tutorial/en/tutorial_update.po")

    # load old revision with new unit
    file_name = "pytest_pootle/data/po/tutorial/en/tutorial_update_old_unit.po"
    _update_from_upload_file(en_tutorial_po, file_name)

    # the unit has been added because its not already obsoleted
    assert len(en_tutorial_po.units) == 2


def _test_store_update_indexes(store, *test_args):
    # make sure indexes are not fooed indexes only have to be unique
    indexes = [x.index for x in store.units]
    assert len(indexes) == len(set(indexes))


def _test_store_update_units_before(*test_args):
    # test what has happened to the units that were present before the update
    (store, units_update, store_revision, resolve_conflict,
     units_before, member, member2) = test_args

    updates = {unit[0]: unit[1] for unit in units_update}

    for unit in units_before:
        updated_unit = store.unit_set.get(unitid=unit.unitid)

        if unit.source not in updates:
            # unit is not in update, target should be left unchanged
            assert updated_unit.target == unit.target
            assert updated_unit.submitted_by == unit.submitted_by

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
                        # unit has changed
                        assert updated_unit.submitted_by == member2

                        # damn mysql microsecond precision
                        if unit.submitted_on.time().microsecond != 0:
                            assert (
                                updated_unit.submitted_on
                                != unit.submitted_on)
                    else:
                        assert updated_unit.submitted_by == unit.submitted_by
                        assert updated_unit.submitted_on == unit.submitted_on
                    assert updated_unit.get_suggestions().count() == 0
                else:
                    # conflict found
                    suggestion = updated_unit.get_suggestions()[0]
                    if resolve_conflict == POOTLE_WINS:
                        assert updated_unit.target == unit.target
                        assert updated_unit.submitted_by == unit.submitted_by
                        assert suggestion.target == updates[unit.source]
                        assert suggestion.user == member2
                    else:
                        assert updated_unit.target == updates[unit.source]
                        assert updated_unit.submitted_by == member2
                        assert suggestion.target == unit.target
                        assert suggestion.user == unit.submitted_by


def _test_store_update_ordering(*test_args):
    (store, units_update, store_revision, resolve_conflict,
     units_before, member, member2) = test_args

    updates = {unit[0]: unit[1] for unit in units_update}
    old_units = {unit.source: unit for unit in units_before}

    # test ordering
    new_unit_list = []
    for unit in units_before:
        add_unit = (not unit.isobsolete()
                    and unit.source not in updates
                    and unit.revision > store_revision)
        if add_unit:
            new_unit_list.append(unit.source)
    for source, target in units_update:
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
    (store, units_update, store_revision, resolve_conflict,
     units_before, member, member2) = test_args

    # test that all the current units should be there
    updates = {unit[0]: unit[1] for unit in units_update}
    old_units = {unit.source: unit for unit in units_before}
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
def test_store_diff(store_diff_tests):
    diff, store, update_units, store_revision = store_diff_tests

    assert diff.db_store == store
    assert diff.file_revision == store_revision
    assert (
        update_units
        == [(x.source, x.target) for x in diff.file_store.units[1:]]
        == [(v['source'], v['target']) for k, v in diff.file_units.items()])
    assert diff.active_units == [x.source for x in store.units]
    assert diff.db_revision == store.get_max_unit_revision()
    assert (
        diff.db_units
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
    assert len(diff.obsoleted_db_units) == obsoleted.count()
    assert all(x in diff.obsoleted_db_units for x in obsoleted)

    assert (
        diff.updated_db_units
        == list(store.units.filter(revision__gt=store_revision)
                           .values_list("source_f", flat=True)))


@pytest.mark.django_db
def test_store_repr():
    store = Store.objects.first()
    assert str(store) == str(store.convert(store.get_file_class()))
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
def test_store_create_by_bad_path():
    project0 = Project.objects.get(code="project0")

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
def test_store_create_by_path():

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
def test_store_create_by_path_with_project():
    project0 = Project.objects.get(code="project0")

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
def test_store_create_by_new_tp_path():
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

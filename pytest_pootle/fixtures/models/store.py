# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from __future__ import print_function

import os
from collections import OrderedDict

import pytest
from pytest_pootle.factories import (
    LanguageDBFactory, StoreDBFactory, TranslationProjectFactory)
from pytest_pootle.utils import create_store, update_store
from translate.storage.factory import getclass


def _update_fuzzy(is_fuzzy, source):
    if source == 'Unit 4':
        return not is_fuzzy
    return is_fuzzy


DEFAULT_STORE_UNITS_1 = [("Unit 1", "Unit 1", False),
                         ("Unit 2", "Unit 2", False)]

DEFAULT_STORE_UNITS_2 = [("Unit 3", "Unit 3", False),
                         ("Unit 4", "Unit 4", True),
                         ("Unit 5", "Unit 5", False)]

DEFAULT_STORE_UNITS_3 = [("Unit 6", "Unit 6", False),
                         ("Unit 7", "Unit 7", True),
                         ("Unit 8", "Unit 8", False)]

UPDATED_STORE_UNITS_1 = [(src, "UPDATED %s" % target, is_fuzzy)
                         for src, target, is_fuzzy
                         in DEFAULT_STORE_UNITS_1]

UPDATED_STORE_UNITS_2 = [(src, "UPDATED %s" % target, _update_fuzzy(is_fuzzy, src))
                         for src, target, is_fuzzy
                         in DEFAULT_STORE_UNITS_2]

UPDATED_STORE_UNITS_3 = [(src, "UPDATED %s" % target, is_fuzzy)
                         for src, target, is_fuzzy
                         in DEFAULT_STORE_UNITS_3]


TEST_UPDATE_PO = "tests/data/po/tutorial/en/tutorial_update.po"
TEST_EVIL_UPDATE_PO = "tests/data/po/tutorial/en/tutorial_update_evil.po"

UPDATE_STORE_TESTS = OrderedDict()
UPDATE_STORE_TESTS['min_empty'] = {"update_store": (0, [])}
UPDATE_STORE_TESTS['min_new_units'] = {
    "update_store": (0, DEFAULT_STORE_UNITS_3)
}

UPDATE_STORE_TESTS['old_empty'] = {"update_store": ("MID", [])}
UPDATE_STORE_TESTS['old_subset_1'] = {
    "update_store": ("MID", UPDATED_STORE_UNITS_1)
}
UPDATE_STORE_TESTS['old_subset_2'] = {
    "update_store": ("MID", UPDATED_STORE_UNITS_2)
}
UPDATE_STORE_TESTS['old_subset_2_pootle_wins'] = {
    "update_store": ("MID", UPDATED_STORE_UNITS_2),
    "fs_wins": False
}
UPDATE_STORE_TESTS['old_same_updated'] = {
    "update_store": ("MID", UPDATED_STORE_UNITS_1 + UPDATED_STORE_UNITS_2)
}
UPDATE_STORE_TESTS['old_same_updated_pootle_wins'] = {
    "update_store": ("MID", UPDATED_STORE_UNITS_1 + UPDATED_STORE_UNITS_2),
    "fs_wins": False
}

UPDATE_STORE_TESTS['old_unobsolete'] = {
    "setup": [DEFAULT_STORE_UNITS_1,
              DEFAULT_STORE_UNITS_2,
              []],
    "update_store": ("MID", UPDATED_STORE_UNITS_1 + UPDATED_STORE_UNITS_2)
}

UPDATE_STORE_TESTS['old_merge'] = {
    "update_store": ("MID", UPDATED_STORE_UNITS_1 + UPDATED_STORE_UNITS_3)
}

UPDATE_STORE_TESTS['max_empty'] = {"update_store": ("MAX", [])}
UPDATE_STORE_TESTS['max_subset'] = {
    "update_store": ("MAX", DEFAULT_STORE_UNITS_1)
}
UPDATE_STORE_TESTS['max_same'] = {
    "update_store": ("MAX", DEFAULT_STORE_UNITS_1 + DEFAULT_STORE_UNITS_2)
}
UPDATE_STORE_TESTS['max_new_units'] = {
    "update_store": ("MAX",
                     (DEFAULT_STORE_UNITS_1
                      + DEFAULT_STORE_UNITS_2
                      + DEFAULT_STORE_UNITS_3))
}
UPDATE_STORE_TESTS['max_change_order'] = {
    "update_store": ("MAX", DEFAULT_STORE_UNITS_2 + DEFAULT_STORE_UNITS_1)
}
UPDATE_STORE_TESTS['max_unobsolete'] = {
    "setup": [DEFAULT_STORE_UNITS_1 + DEFAULT_STORE_UNITS_2,
              DEFAULT_STORE_UNITS_1],
    "update_store": ("MAX", DEFAULT_STORE_UNITS_1 + DEFAULT_STORE_UNITS_2)
}


UPDATE_STORE_TESTS['max_obsolete'] = {
    "setup": [DEFAULT_STORE_UNITS_1,
              (DEFAULT_STORE_UNITS_1
               + DEFAULT_STORE_UNITS_2
               + DEFAULT_STORE_UNITS_3)],
    "update_store": ("MAX", DEFAULT_STORE_UNITS_1 + DEFAULT_STORE_UNITS_3)
}


def _setup_store_test(store, member, member2, test):
    from pootle_store.constants import POOTLE_WINS, SOURCE_WINS

    setup = test.get("setup", None)

    if setup is None:
        setup = [(DEFAULT_STORE_UNITS_1),
                 (DEFAULT_STORE_UNITS_1 + DEFAULT_STORE_UNITS_2)]

    for units in setup:
        store_revision = store.get_max_unit_revision()
        print("setup store: %s %s" % (store_revision, units))
        update_store(store, store_revision=store_revision, units=units,
                     user=member)
        for unit in store.units:
            comment = ("Set up unit(%s) with store_revision: %s"
                       % (unit.source_f, store_revision))
            _create_comment_on_unit(unit, member, comment)

    store_revision, units_update = test["update_store"]
    units_before = [
        (unit, unit.change)
        for unit in store.unit_set.select_related("change").all().order_by("index")]

    fs_wins = test.get("fs_wins", True)
    if fs_wins:
        resolve_conflict = SOURCE_WINS
    else:
        resolve_conflict = POOTLE_WINS

    if store_revision == "MAX":
        store_revision = store.get_max_unit_revision()

    elif store_revision == "MID":
        revisions = [unit.revision for unit, change in units_before]
        store_revision = sum(revisions) / len(revisions)

    return (store, units_update, store_revision, resolve_conflict,
            units_before, member, member2)


@pytest.fixture(params=UPDATE_STORE_TESTS.keys())
def store_diff_tests(request, tp0, member, member2):
    from pootle_store.contextmanagers import update_store_after
    from pootle_store.diff import StoreDiff

    store = StoreDBFactory(
        translation_project=tp0,
        parent=tp0.directory)

    with update_store_after(store):
        test = _setup_store_test(store, member, member2,
                                 UPDATE_STORE_TESTS[request.param])
    test_store = create_store(units=test[1])
    return [StoreDiff(test[0], test_store, test[2])] + list(test[:3])


@pytest.fixture(params=UPDATE_STORE_TESTS.keys())
def param_update_store_test(request, tp0, member, member2):
    from pootle.core.contextmanagers import keep_data
    from pootle.core.signals import update_data

    store = StoreDBFactory(
        translation_project=tp0,
        parent=tp0.directory)

    with keep_data():
        test = _setup_store_test(
            store, member, member2,
            UPDATE_STORE_TESTS[request.param])
    update_data.send(store.__class__, instance=store)

    with keep_data():
        update_store(
            test[0],
            units=test[1],
            store_revision=test[2],
            user=member2,
            resolve_conflict=test[3])
    update_data.send(store.__class__, instance=store)

    return test


def _require_store(tp, po_dir, name):
    """Helper to get/create a new store."""
    from pootle_store.constants import PARSED
    from pootle_store.models import Store

    parent_dir = tp.directory
    pootle_path = tp.pootle_path + name

    file_path = (
        tp.real_path
        and os.path.join(po_dir, tp.real_path, name))

    try:
        store = Store.objects.get(
            pootle_path=pootle_path,
            translation_project=tp,
        )
    except Store.DoesNotExist:
        store = Store.objects.create_by_path(
            file=file_path,
            create_tp=False,
            create_directory=False,
            pootle_path=(
                "%s%s"
                % (parent_dir.pootle_path,
                   name)))
    if store.file.exists():
        if store.state < PARSED:
            store.update(store.file.store)

    return store


def _create_submission_and_suggestion(store, user,
                                      units=None,
                                      suggestion="SUGGESTION"):
    from pootle.core.delegate import review
    from pootle.core.models import Revision
    from pootle_store.models import Suggestion

    # Update store as user
    if units is None:
        units = [("Hello, world", "Hello, world UPDATED", False)]
    update_store(
        store,
        units,
        user=user,
        store_revision=Revision.get() + 1)

    # Add a suggestion
    unit = store.units[0]
    review.get(Suggestion)().add(unit, suggestion, user)
    return unit


def _create_comment_on_unit(unit, user, comment):
    from pootle_statistics.models import (Submission, SubmissionFields,
                                          SubmissionTypes)

    unit.translator_comment = comment
    unit.save(user=user)
    sub = Submission(
        creation_time=unit.change.commented_on,
        translation_project=unit.store.translation_project,
        submitter=user,
        unit=unit,
        field=SubmissionFields.COMMENT,
        type=SubmissionTypes.WEB,
        new_value=comment,
    )
    sub.save()


def _mark_unit_fuzzy(unit, user):
    from pootle_store.constants import FUZZY
    from pootle_statistics.models import (Submission, SubmissionFields,
                                          SubmissionTypes)
    unit.markfuzzy()
    unit.save()
    sub = Submission(
        creation_time=unit.mtime,
        translation_project=unit.store.translation_project,
        submitter=user,
        unit=unit,
        field=SubmissionFields.STATE,
        type=SubmissionTypes.WEB,
        old_value=unit.state,
        new_value=FUZZY,
    )
    sub.save()


def _make_member_updates(store, member):
    from pootle_store.contextmanagers import update_store_after

    # Member updates first unit, adding a suggestion, and marking unit as fuzzy
    with update_store_after(store):
        _create_submission_and_suggestion(store, member)
        _create_comment_on_unit(store.units[0], member, "NICE COMMENT")
        _mark_unit_fuzzy(store.units[0], member)


@pytest.fixture
def af_tutorial_po(po_directory, settings, afrikaans_tutorial):
    """Require the /af/tutorial/tutorial.po store."""
    return _require_store(afrikaans_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def en_tutorial_po(po_directory, settings, english_tutorial):
    """Require the /en/tutorial/tutorial.po store."""
    return _require_store(english_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def en_tutorial_po_member_updated(po_directory, settings, english_tutorial, member):
    """Require the /en/tutorial/tutorial.po store."""
    store = _require_store(english_tutorial,
                           settings.POOTLE_TRANSLATION_DIRECTORY,
                           'tutorial.po')
    _make_member_updates(store, member)
    return store


@pytest.fixture
def it_tutorial_po(po_directory, settings, italian_tutorial):
    """Require the /it/tutorial/tutorial.po store."""
    return _require_store(italian_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def issue_2401_po(po_directory, settings, afrikaans_tutorial):
    """Require the /af/tutorial/issue_2401.po store."""
    return _require_store(afrikaans_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'issue_2401.po')


@pytest.fixture
def store_po(tp0):
    """An empty Store in the /language0/project0 TP"""
    from pootle_translationproject.models import TranslationProject

    tp = TranslationProject.objects.get(
        project__code="project0",
        language__code="language0")

    store = StoreDBFactory(
        parent=tp.directory,
        translation_project=tp,
        name="test_store.po")
    return store


@pytest.fixture(scope="session")
def complex_ttk(test_fs):
    with test_fs.open(("data", "po", "complex.po")) as f:
        ttk = getclass(f)(f.read())
    return ttk


@pytest.fixture
def complex_po():
    from pootle_store.models import Store

    return Store.objects.get(name="complex.po")


@pytest.fixture
def no_complex_po_():
    from pootle_store.models import Store

    Store.objects.get(name="complex.po").delete()


@pytest.fixture
def diffable_stores(complex_po, request):
    from pootle.core.delegate import format_diffs
    from pootle_store.models import Store
    from pootle_translationproject.models import TranslationProject

    start_receivers = format_diffs.receivers

    tp = TranslationProject.objects.get(
        language=complex_po.translation_project.language,
        project__code="project1")
    other_po = Store.objects.create(
        name="complex.po",
        translation_project=tp,
        parent=tp.directory,
        pootle_path=complex_po.pootle_path.replace("project0", "project1"))
    other_po.update(other_po.deserialize(complex_po.serialize()))

    def _reset_format_diffs():
        format_diffs.receivers = start_receivers
    request.addfinalizer(_reset_format_diffs)
    return complex_po, other_po


@pytest.fixture
def dummy_store_structure_syncer():
    from pootle_store.syncer import StoreSyncer
    from django.utils.functional import cached_property

    class DummyUnit(object):

        def __init__(self, unit, expected):
            self.unit = unit
            self.expected = expected

        def convert(self, unit_class):
            assert unit_class == self.expected["unit_class"]
            return self.unit, unit_class

    class DummyDiskStore(object):

        def __init__(self, expected):
            self.expected = expected
            self.UnitClass = expected["unit_class"]

        @cached_property
        def _units(self):
            for unit in self.expected["new_units"]:
                yield unit

        def addunit(self, newunit):
            unit, unit_class = newunit
            assert unit == self._units.next().unit
            assert unit_class == self.UnitClass

    class DummyStoreSyncer(StoreSyncer):

        def __init__(self, *args, **kwargs):
            self.expected = kwargs.pop("expected")
            super(DummyStoreSyncer, self).__init__(*args, **kwargs)

        @cached_property
        def _units(self):
            for unit in self.expected["obsolete_units"]:
                yield unit

        def obsolete_unit(self, unit, conservative):
            assert conservative == self.expected["conservative"]
            assert unit == self._units.next()
            return self.expected["obsolete_delete"]

    return DummyStoreSyncer, DummyDiskStore, DummyUnit


@pytest.fixture
def dummy_store_syncer_units():
    from pootle_store.syncer import StoreSyncer

    class DummyStore(object):

        def __init__(self, expected):
            self.expected = expected

        def findid_bulk(self, uids):
            return uids

    class DummyStoreSyncer(StoreSyncer):

        def __init__(self, *args, **kwargs):
            self.expected = kwargs.pop("expected")
            super(DummyStoreSyncer, self).__init__(*args, **kwargs)
            self.store = DummyStore(self.expected)

        @property
        def dbid_index(self):
            return self.expected["db_ids"]

    return DummyStoreSyncer


@pytest.fixture
def dummy_store_syncer():
    from pootle_store.syncer import StoreSyncer

    class DummyDiskStore(object):

        def __init__(self, expected):
            self.expected = expected

        def getids(self):
            return self.expected["disk_ids"]

    class DummyStoreSyncer(StoreSyncer):

        def __init__(self, *args, **kwargs):
            self.expected = kwargs.pop("expected")
            super(DummyStoreSyncer, self).__init__(*args, **kwargs)

        @property
        def dbid_index(self):
            return self.expected["db_index"]

        def get_units_to_obsolete(self, disk_store, old_ids_, new_ids_):
            return self.expected["obsolete_units"]

        def get_new_units(self, old_ids, new_ids):
            assert old_ids == set(self.expected["disk_ids"])
            assert new_ids == set(self.expected["db_index"].keys())
            return self.expected["new_units"]

        def get_common_units(self, units_, last_revision, conservative):
            assert last_revision == self.expected["last_revision"]
            assert conservative == self.expected["conservative"]
            return self.expected["common_units"]

        def update_structure(self, disk_store, obsolete_units,
                             new_units, conservative):
            assert obsolete_units == self.expected["obsolete_units"]
            assert new_units == self.expected["new_units"]
            assert conservative == self.expected["conservative"]
            return self.expected["structure_changed"]

        def sync_units(self, disk_store, units):
            assert units == self.expected["common_units"]
            return self.expected["changes"]

    expected = dict(
        last_revision=23,
        conservative=True,
        update_structure=False,
        disk_ids=[5, 6, 7],
        db_index={"a": 1, "b": 2, "c": 3},
        structure_changed=(8, 9, 10),
        obsolete_units=["obsolete", "units"],
        new_units=["new", "units"],
        common_units=["common", "units"],
        changes=["some", "changes"])
    return DummyStoreSyncer, DummyDiskStore, expected


@pytest.fixture
def store0(tp0):
    stores = tp0.stores.select_related(
        "data",
        "parent",
        "filetype__extension",
        "filetype__template_extension")
    return stores.get(name="store0.po")


@pytest.fixture
def ordered_po(test_fs, tp0):
    """Create a store with ordered units."""

    store = StoreDBFactory(
        name="ordered.po",
        translation_project=tp0,
        parent=tp0.directory)
    with test_fs.open("data/po/ordered.po") as src:
        store.update(store.deserialize(src.read()))
    return store


@pytest.fixture
def numbered_po(test_fs, project0):
    """Create a store with numbered units."""

    tp = TranslationProjectFactory(
        project=project0,
        language=LanguageDBFactory())
    store = StoreDBFactory(
        name="numbered.po",
        translation_project=tp,
        parent=tp.directory)
    with test_fs.open("data/po/1234.po") as src:
        store.update(store.deserialize(src.read()))
    return store


@pytest.fixture
def ordered_update_ttk(test_fs, store0):
    with test_fs.open("data/po/ordered_updated.po") as src:
        ttk = store0.deserialize(src.read())
    return ttk

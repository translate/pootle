# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from collections import OrderedDict

import pytest

from translate.storage.factory import getclass

from django.utils import timezone

from pytest_pootle.utils import create_store, update_store


DEFAULT_STORE_UNITS_1 = [("Unit 1", "Unit 1"),
                         ("Unit 2", "Unit 2")]

DEFAULT_STORE_UNITS_2 = [("Unit 3", "Unit 3"),
                         ("Unit 4", "Unit 4"),
                         ("Unit 5", "Unit 5")]

DEFAULT_STORE_UNITS_3 = [("Unit 6", "Unit 6"),
                         ("Unit 7", "Unit 7"),
                         ("Unit 8", "Unit 8")]

UPDATED_STORE_UNITS_1 = [(src, "UPDATED %s" % target)
                         for src, target
                         in DEFAULT_STORE_UNITS_1]

UPDATED_STORE_UNITS_2 = [(src, "UPDATED %s" % target)
                         for src, target
                         in DEFAULT_STORE_UNITS_2]

UPDATED_STORE_UNITS_3 = [(src, "UPDATED %s" % target)
                         for src, target
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
    from pootle_store.models import FILE_WINS, POOTLE_WINS

    setup = test.get("setup", None)

    if setup is None:
        setup = [(DEFAULT_STORE_UNITS_1),
                 (DEFAULT_STORE_UNITS_1 + DEFAULT_STORE_UNITS_2)]

    for units in setup:
        store_revision = store.get_max_unit_revision()
        print "setup store: %s %s" % (store_revision, units)
        update_store(store, store_revision=store_revision, units=units,
                     user=member)
        for unit in store.units:
            comment = ("Set up unit(%s) with store_revision: %s"
                       % (unit.source_f, store_revision))
            _create_comment_on_unit(unit, member, comment)

    store_revision, units_update = test["update_store"]
    units_before = [
        unit for unit in store.unit_set.all().order_by("index")]

    fs_wins = test.get("fs_wins", True)
    if fs_wins:
        resolve_conflict = FILE_WINS
    else:
        resolve_conflict = POOTLE_WINS

    if store_revision == "MAX":
        store_revision = store.get_max_unit_revision()

    elif store_revision == "MID":
        revisions = [unit.revision for unit in units_before]
        store_revision = sum(revisions) / len(revisions)

    return (store, units_update, store_revision, resolve_conflict,
            units_before, member, member2)


@pytest.fixture(params=UPDATE_STORE_TESTS.keys())
def store_diff_tests(request, en_tutorial_po, member, member2):
    from pootle_store.models import StoreDiff

    test = _setup_store_test(en_tutorial_po, member, member2,
                             UPDATE_STORE_TESTS[request.param])
    test_store = create_store(units=test[1])
    return [StoreDiff(test[0], test_store, test[2])] + list(test[:3])


@pytest.fixture(params=UPDATE_STORE_TESTS.keys())
def param_update_store_test(request, en_tutorial_po, member, member2):
    test = _setup_store_test(en_tutorial_po, member, member2,
                             UPDATE_STORE_TESTS[request.param])
    update_store(test[0],
                 units=test[1],
                 store_revision=test[2],
                 user=member2,
                 resolve_conflict=test[3])
    return test


def _require_store(tp, po_dir, name):
    """Helper to get/create a new store."""
    from pootle_store.models import PARSED, Store

    file_path = os.path.join(po_dir, tp.real_path, name)
    parent_dir = tp.directory
    pootle_path = tp.pootle_path + name

    try:
        store = Store.objects.get(
            pootle_path=pootle_path,
            translation_project=tp,
        )
    except Store.DoesNotExist:
        store = Store.objects.create(
            file=file_path,
            parent=parent_dir,
            name=name,
            translation_project=tp,
        )

    if store.file.exists():
        if store.state < PARSED:
            store.update(store.file.store)

    return store


def _create_submission_and_suggestion(store, user,
                                      units=None,
                                      suggestion="SUGGESTION"):

    from pootle.core.models import Revision

    # Update store as user
    if units is None:
        units = [("Hello, world", "Hello, world UPDATED")]
    update_store(
        store,
        units,
        user=user,
        store_revision=Revision.get() + 1)

    # Add a suggestion
    unit = store.units[0]
    unit.add_suggestion(suggestion, user=user)
    return unit


def _create_comment_on_unit(unit, user, comment):
    from pootle_statistics.models import (Submission, SubmissionFields,
                                          SubmissionTypes)

    unit.translator_comment = comment
    unit.commented_on = timezone.now()
    unit.commented_by = user
    sub = Submission(
        creation_time=unit.commented_on,
        translation_project=unit.store.translation_project,
        submitter=user,
        unit=unit,
        store=unit.store,
        field=SubmissionFields.COMMENT,
        type=SubmissionTypes.NORMAL,
        new_value=comment,
    )
    sub.save()
    unit._comment_updated = True
    unit.save()


def _mark_unit_fuzzy(unit, user):
    from pootle_store.util import FUZZY
    from pootle_statistics.models import (Submission, SubmissionFields,
                                          SubmissionTypes)
    sub = Submission(
        creation_time=unit.commented_on,
        translation_project=unit.store.translation_project,
        submitter=user,
        unit=unit,
        store=unit.store,
        field=SubmissionFields.STATE,
        type=SubmissionTypes.NORMAL,
        old_value=unit.state,
        new_value=FUZZY,
    )
    sub.save()
    unit.markfuzzy()
    unit._state_updated = True
    unit.save()


def _make_member_updates(store, member):
    # Member updates first unit, adding a suggestion, and marking unit as fuzzy
    _create_submission_and_suggestion(store, member)
    _create_comment_on_unit(store.units[0], member, "NICE COMMENT")
    _mark_unit_fuzzy(store.units[0], member)


@pytest.fixture
def af_tutorial_po(settings, afrikaans_tutorial, system):
    """Require the /af/tutorial/tutorial.po store."""
    return _require_store(afrikaans_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def en_tutorial_po(settings, english_tutorial, system):
    """Require the /en/tutorial/tutorial.po store."""
    return _require_store(english_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def en_tutorial_po_no_file(settings, english_tutorial, system):
    """Require an empty store."""
    return _require_store(english_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'no_file.po')


@pytest.fixture
def en_tutorial_po_member_updated(settings, english_tutorial,
                                  system, member):
    """Require the /en/tutorial/tutorial.po store."""
    store = _require_store(english_tutorial,
                           settings.POOTLE_TRANSLATION_DIRECTORY,
                           'tutorial.po')
    _make_member_updates(store, member)
    return store


@pytest.fixture
def it_tutorial_po(settings, italian_tutorial, system):
    """Require the /it/tutorial/tutorial.po store."""
    return _require_store(italian_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def af_tutorial_subdir_po(settings, afrikaans_tutorial, system):
    """Require the /af/tutorial/subdir/tutorial.po store."""
    return _require_store(afrikaans_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'subdir/tutorial.po')


@pytest.fixture
def issue_2401_po(settings, afrikaans_tutorial, system):
    """Require the /af/tutorial/issue_2401.po store."""
    return _require_store(afrikaans_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'issue_2401.po')


@pytest.fixture
def test_get_units_po(settings, afrikaans_tutorial, system):
    """Require the /af/tutorial/test_get_units.po store."""
    return _require_store(afrikaans_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'test_get_units.po')


@pytest.fixture
def fr_tutorial_subdir_to_remove_po(settings, french_tutorial, system):
    """Require the /fr/tutorial/subdir_to_remove/tutorial.po store."""
    return _require_store(french_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'subdir_to_remove/tutorial.po')


@pytest.fixture
def fr_tutorial_remove_sync_po(settings, french_tutorial, system):
    """Require the /fr/tutorial/remove_sync_tutorial.po store."""
    return _require_store(french_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'remove_sync_tutorial.po')


@pytest.fixture
def es_tutorial_subdir_remove_po(settings, spanish_tutorial, system):
    """Require the /es/tutorial/subdir/remove_tutorial.po store."""
    return _require_store(spanish_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'subdir/remove_tutorial.po')


@pytest.fixture
def ru_tutorial_po(settings, russian_tutorial, system):
    """Require the /ru/tutorial/tutorial.po store."""
    return _require_store(russian_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY, 'tutorial.po')


@pytest.fixture
def ru_update_save_changed_units_po(settings, russian_tutorial, system):
    """Require the /ru/tutorial/tutorial.po store."""
    return _require_store(russian_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'update_save_changed_units.po')


@pytest.fixture
def ru_update_set_last_sync_revision_po(settings, russian_tutorial, system):
    """Require the /ru/tutorial/tutorial.po store."""
    return _require_store(russian_tutorial,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'update_set_last_sync_revision.po')


@pytest.fixture
def af_vfolder_test_browser_defines_po(settings, afrikaans_vfolder_test,
                                       system):
    """Require the /af/vfolder_test/browser/defines.po store."""
    return _require_store(afrikaans_vfolder_test,
                          settings.POOTLE_TRANSLATION_DIRECTORY,
                          'browser/defines.po')


@pytest.fixture
def store_po():
    """An empty Store in the /language0/project0 TP"""
    from pootle_translationproject.models import TranslationProject

    from pytest_pootle.factories import StoreDBFactory

    tp = TranslationProject.objects.get(
        project__code="project0",
        language__code="language0")

    store = StoreDBFactory(
        parent=tp.directory,
        translation_project=tp,
        name="test_store.po")
    return store


@pytest.fixture
def complex_po(test_fs):
    """A Store with some complex Units"""
    from pootle_translationproject.models import TranslationProject

    from pytest_pootle.factories import StoreDBFactory

    tp = TranslationProject.objects.get(
        project__code="project0",
        language__code="language0")

    store = StoreDBFactory(
        parent=tp.directory,
        translation_project=tp,
        name="complex_store.po")

    with test_fs.open(("data", "po", "complex.po")) as f:
        ttk = getclass(f)(f.read())

    store.update(ttk)
    return store

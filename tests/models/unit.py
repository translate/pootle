#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest
from translate.storage import factory

from django.contrib.auth import get_user_model
from django.utils import timezone

from pootle.core.mixins.treeitem import CachedMethods
from pootle_store.util import FUZZY, TRANSLATED, UNTRANSLATED
from pootle_store.models import Unit


User = get_user_model()


def _update_translation(store, item, new_values, sync=True):
    unit = store.getitem(item)

    if 'target' in new_values:
        unit.target = new_values['target']

    if 'fuzzy' in new_values:
        unit.markfuzzy(new_values['fuzzy'])

    if 'translator_comment' in new_values:
        unit.translator_comment = new_values['translator_comment']
        unit._comment_updated = True

    unit.submitted_on = timezone.now()
    unit.submitted_by = User.objects.get_system_user()
    unit.save()

    if sync:
        store.sync()

    return store.getitem(item)


@pytest.mark.django_db
def test_getorig(af_tutorial_po):
    """Tests that the in-DB Store and on-disk Store match by checking that
    units match in order.
    """
    for db_unit in af_tutorial_po.units.iterator():
        store_unit = db_unit.getorig()
        assert db_unit.getid() == store_unit.getid()


@pytest.mark.django_db
def test_convert(af_tutorial_po):
    """Tests that in-DB and on-disk units match after format conversion."""
    for db_unit in af_tutorial_po.units.iterator():
        if db_unit.hasplural() and not db_unit.istranslated():
            # Skip untranslated plural units, they will always look different
            continue

        store_unit = db_unit.getorig()
        newunit = db_unit.convert(af_tutorial_po.file.store.UnitClass)

        assert str(newunit) == str(store_unit)


@pytest.mark.django_db
def test_update_target(af_tutorial_po):
    """Tests that target changes are properly sync'ed to disk."""
    db_unit = _update_translation(af_tutorial_po, 0, {'target': u'samaka'})
    store_unit = db_unit.getorig()

    assert db_unit.target == u'samaka'
    assert db_unit.target == store_unit.target

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert db_unit.target == po_file.units[db_unit.index].target


@pytest.mark.django_db
def test_empty_plural_target(af_tutorial_po):
    """Tests empty plural targets are not deleted."""
    db_unit = _update_translation(af_tutorial_po, 2, {'target': [u'samaka']})
    store_unit = db_unit.getorig()
    assert len(store_unit.target.strings) == 2

    db_unit = _update_translation(af_tutorial_po, 2, {'target': u''})
    assert len(store_unit.target.strings) == 2


@pytest.mark.django_db
def test_update_plural_target(af_tutorial_po):
    """Tests plural translations are stored and sync'ed."""
    db_unit = _update_translation(
        af_tutorial_po, 2,
        {'target': [u'samaka', u'samak']})
    store_unit = db_unit.getorig()

    assert db_unit.target.strings == [u'samaka', u'samak']
    assert db_unit.target.strings == store_unit.target.strings

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert (
        db_unit.target.strings
        == po_file.units[db_unit.index].target.strings)

    assert db_unit.target == u'samaka'
    assert db_unit.target == store_unit.target
    assert db_unit.target == po_file.units[db_unit.index].target


@pytest.mark.django_db
def test_update_plural_target_dict(af_tutorial_po):
    """Tests plural translations are stored and sync'ed (dict version)."""
    db_unit = _update_translation(
        af_tutorial_po, 2,
        {'target': {0: u'samaka', 1: u'samak'}})
    store_unit = db_unit.getorig()

    assert db_unit.target.strings == [u'samaka', u'samak']
    assert db_unit.target.strings == store_unit.target.strings

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert (
        db_unit.target.strings
        == po_file.units[db_unit.index].target.strings)

    assert db_unit.target == u'samaka'
    assert db_unit.target == store_unit.target
    assert db_unit.target == po_file.units[db_unit.index].target


@pytest.mark.django_db
def test_update_fuzzy(af_tutorial_po):
    """Tests fuzzy state changes are stored and sync'ed."""
    db_unit = _update_translation(
        af_tutorial_po, 0,
        {'target': u'samaka', 'fuzzy': True})
    store_unit = db_unit.getorig()

    assert db_unit.isfuzzy()
    assert db_unit.isfuzzy() == store_unit.isfuzzy()

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert db_unit.isfuzzy() == po_file.units[db_unit.index].isfuzzy()

    db_unit = _update_translation(af_tutorial_po, 0, {'fuzzy': False})
    store_unit = db_unit.getorig()

    assert not db_unit.isfuzzy()
    assert db_unit.isfuzzy() == store_unit.isfuzzy()

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert db_unit.isfuzzy() == po_file.units[db_unit.index].isfuzzy()


@pytest.mark.django_db
def test_update_comment(af_tutorial_po):
    """Tests translator comments are stored and sync'ed."""
    db_unit = _update_translation(
        af_tutorial_po, 0,
        {'translator_comment': u'7amada'})
    store_unit = db_unit.getorig()

    assert db_unit.getnotes(origin='translator') == u'7amada'
    assert (
        db_unit.getnotes(origin='translator')
        == store_unit.getnotes(origin='translator'))

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert (
        db_unit.getnotes(origin='translator')
        == po_file.units[db_unit.index].getnotes(origin='translator'))


@pytest.mark.django_db
def test_add_suggestion(af_tutorial_po, system):
    """Tests adding new suggestions to units."""
    untranslated_unit = af_tutorial_po.getitem(0)
    translated_unit = af_tutorial_po.getitem(1)
    suggestion_text = 'foo bar baz'

    # Empty suggestion is not recorded
    sugg, added = untranslated_unit.add_suggestion('')
    assert sugg is None
    assert not added

    # Existing translation can't be added as a suggestion
    sugg, added = translated_unit.add_suggestion(translated_unit.target)
    assert sugg is None
    assert not added

    # Add new suggestion
    sugg, added = untranslated_unit.add_suggestion(suggestion_text)
    assert sugg is not None
    assert added
    assert len(untranslated_unit.get_suggestions()) == 1

    # Already-suggested text can't be suggested again
    sugg, added = untranslated_unit.add_suggestion(suggestion_text)
    assert sugg is not None
    assert not added
    assert len(untranslated_unit.get_suggestions()) == 1

    # Removing a suggestion should allow suggesting the same text again
    tp = untranslated_unit.store.translation_project
    untranslated_unit.reject_suggestion(sugg, tp, system)
    assert len(untranslated_unit.get_suggestions()) == 0

    sugg, added = untranslated_unit.add_suggestion(suggestion_text)
    assert sugg is not None
    assert added
    assert len(untranslated_unit.get_suggestions()) == 1


@pytest.mark.django_db
def test_accept_suggestion_changes_state(issue_2401_po, system):
    """Tests that accepting a suggestion will change the state of the unit."""
    tp = issue_2401_po.translation_project

    # First test with an untranslated unit
    unit = issue_2401_po.getitem(0)
    assert unit.state == UNTRANSLATED

    suggestion, created = unit.add_suggestion('foo')
    assert unit.state == UNTRANSLATED

    unit.accept_suggestion(suggestion, tp, system)
    assert unit.state == TRANSLATED

    # Let's try with a translated unit now
    unit = issue_2401_po.getitem(1)
    assert unit.state == TRANSLATED

    suggestion, created = unit.add_suggestion('bar')
    assert unit.state == TRANSLATED

    unit.accept_suggestion(suggestion, tp, system)
    assert unit.state == TRANSLATED

    # And finally a fuzzy unit
    unit = issue_2401_po.getitem(2)
    assert unit.state == FUZZY

    suggestion, created = unit.add_suggestion('baz')
    assert unit.state == FUZZY

    unit.accept_suggestion(suggestion, tp, system)
    assert unit.state == TRANSLATED


@pytest.mark.django_db
def test_accept_suggestion_update_wordcount(it_tutorial_po, system):
    """Tests that accepting a suggestion for an untranslated unit will
    change the wordcount stats of the unit's store.
    """

    # Parse store
    it_tutorial_po.update(it_tutorial_po.file.store)

    untranslated_unit = it_tutorial_po.getitem(0)
    suggestion_text = 'foo bar baz'

    sugg, added = untranslated_unit.add_suggestion(suggestion_text)
    assert sugg is not None
    assert added
    assert len(untranslated_unit.get_suggestions()) == 1
    assert it_tutorial_po.get_cached(CachedMethods.SUGGESTIONS) == 1
    assert (
        it_tutorial_po.get_cached(CachedMethods.WORDCOUNT_STATS)['translated']
        == 1)
    assert untranslated_unit.state == UNTRANSLATED
    untranslated_unit.accept_suggestion(sugg,
                                        it_tutorial_po.translation_project,
                                        system)
    assert untranslated_unit.state == TRANSLATED
    assert (
        it_tutorial_po.get_cached(CachedMethods.WORDCOUNT_STATS)['translated']
        == 2)


@pytest.mark.django_db
def test_unit_repr():
    unit = Unit.objects.first()
    assert str(unit) == str(unit.convert(unit.get_unit_class()))
    assert unicode(unit) == unicode(unit.source)

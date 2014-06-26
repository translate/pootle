#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009, 2013 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import pytest

from translate.storage import factory


def _update_translation(store, item, new_values):
    unit = store.getitem(item)

    if 'target' in new_values:
        unit.target = new_values['target']
        if "fuzzy" not in new_values:
            unit.state = 200

    if 'fuzzy' in new_values:
        unit.markfuzzy(new_values['fuzzy'])

    if 'translator_comment' in new_values:
        unit.translator_comment = new_values['translator_comment']

    if new_values.get("refresh_stats"):
        unit._target_updated = True
        # Will be updated on save()

    unit.save()
    store.sync()

    return store.getitem(item)


def test_getorig(af_tutorial_po):
    """Tests that the in-DB Store and on-disk Store match by checking that
    units match in order.
    """
    for db_unit in af_tutorial_po.units.iterator():
        store_unit = db_unit.getorig()
        assert db_unit.getid() == store_unit.getid()


def test_convert(af_tutorial_po):
    """Tests that in-DB and on-disk units match after format conversion."""
    for db_unit in af_tutorial_po.units.iterator():
        if db_unit.hasplural() and not db_unit.istranslated():
            # Skip untranslated plural units, they will always look
            # different
            continue

        store_unit = db_unit.getorig()
        newunit = db_unit.convert(af_tutorial_po.file.store.UnitClass)

        assert str(newunit) == str(store_unit)


@pytest.mark.xfail
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


@pytest.mark.xfail
@pytest.mark.django_db
def test_update_plural_target(af_tutorial_po):
    """Tests plural translations are stored and sync'ed."""
    db_unit = _update_translation(af_tutorial_po, 2,
                                 {'target': [u'samaka', u'samak']})
    store_unit = db_unit.getorig()

    assert db_unit.target.strings == [u'samaka', u'samak']
    assert db_unit.target.strings == store_unit.target.strings

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert db_unit.target.strings == po_file.units[db_unit.index].target.strings

    assert db_unit.target == u'samaka'
    assert db_unit.target == store_unit.target
    assert db_unit.target == po_file.units[db_unit.index].target


@pytest.mark.xfail
@pytest.mark.django_db
def test_update_plural_target_dict(af_tutorial_po):
    """Tests plural translations are stored and sync'ed (dict version)."""
    db_unit = _update_translation(af_tutorial_po, 2,
                                 {'target': {0: u'samaka', 1: u'samak'}})
    store_unit = db_unit.getorig()

    assert db_unit.target.strings == [u'samaka', u'samak']
    assert db_unit.target.strings == store_unit.target.strings

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert db_unit.target.strings == po_file.units[db_unit.index].target.strings

    assert db_unit.target == u'samaka'
    assert db_unit.target == store_unit.target
    assert db_unit.target == po_file.units[db_unit.index].target


@pytest.mark.xfail
@pytest.mark.django_db
def test_update_fuzzy(af_tutorial_po):
    """Tests fuzzy state changes are stored and sync'ed."""
    db_unit = _update_translation(af_tutorial_po, 0,
                                 {'target': u'samaka', 'fuzzy': True})
    store_unit = db_unit.getorig()

    assert db_unit.isfuzzy() == True
    assert db_unit.isfuzzy() == store_unit.isfuzzy()

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert db_unit.isfuzzy() == po_file.units[db_unit.index].isfuzzy()

    db_unit = _update_translation(af_tutorial_po, 0, {'fuzzy': False})
    store_unit = db_unit.getorig()

    assert db_unit.isfuzzy() == False
    assert db_unit.isfuzzy() == store_unit.isfuzzy()

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert db_unit.isfuzzy() == po_file.units[db_unit.index].isfuzzy()


@pytest.mark.xfail
@pytest.mark.django_db
def test_update_comment(af_tutorial_po):
    """Tests translator comments are stored and sync'ed."""
    db_unit = _update_translation(af_tutorial_po, 0,
                                 {'translator_comment': u'7amada'})
    store_unit = db_unit.getorig()

    assert db_unit.getnotes(origin='translator') == u'7amada'
    assert db_unit.getnotes(origin='translator') == \
            store_unit.getnotes(origin='translator')

    po_file = factory.getobject(af_tutorial_po.file.path)
    assert db_unit.getnotes(origin='translator') == \
            po_file.units[db_unit.index].getnotes(origin='translator')


@pytest.mark.django_db
def test_stats_counting(af_tutorial_po):
    unit = _update_translation(af_tutorial_po, 0, {"refresh_stats": True})
    initial_translated = af_tutorial_po.translated_wordcount
    initial_wordcount = af_tutorial_po.total_wordcount
    db_unit = _update_translation(af_tutorial_po, 0, {'target': u'samaka'})
    # assert af_tutorial_po.translated_wordcount == initial_translated + 1  # Flaky
    assert af_tutorial_po.total_wordcount == initial_wordcount

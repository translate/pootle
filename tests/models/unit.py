# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from translate.storage.factory import getclass
from translate.storage.pypo import pounit
from translate.storage.statsdb import wordcount as counter

from django.contrib.auth import get_user_model

from pootle.core.delegate import review, wordcount
from pootle.core.plugin import getter
from pootle_fs.utils import FSPlugin
from pootle_store.constants import FUZZY, OBSOLETE, TRANSLATED, UNTRANSLATED
from pootle_store.models import Suggestion, Unit
from pootle_store.syncer import UnitSyncer


User = get_user_model()


def _sync_translations(db_unit):
    store = db_unit.store
    tp = store.translation_project
    project = tp.project
    language = tp.language
    plugin = FSPlugin(project)
    plugin.fetch()
    plugin.sync()
    file_store = db_unit.store.deserialize(
        open(os.path.join(
            plugin.fs_url,
            language.code,
            store.name)).read())
    file_unit = file_store.findid(db_unit.getid())
    return file_store, file_unit


@pytest.mark.django_db
def test_getorig(project0_nongnu, af_tutorial_po):
    """Tests that the in-DB Store and on-disk Store match by checking that
    units match in order.
    """
    file_store, __ = _sync_translations(af_tutorial_po.units.first())
    for i, db_unit in enumerate(af_tutorial_po.units.iterator()):
        file_unit = file_store.units[i + 1]
        assert db_unit.getid() == file_unit.getid()


@pytest.mark.django_db
def test_convert(project0_nongnu, af_tutorial_po):
    """Tests that in-DB and on-disk units match after format conversion."""
    # db unit doesnt have plural form by default, so add
    plural_unit = af_tutorial_po.units.last()
    plural_unit.target = [u'samaka', u'samak']
    plural_unit.save()
    file_store, __ = _sync_translations(af_tutorial_po.units.first())
    for db_unit in af_tutorial_po.units.iterator():
        file_unit = file_store.findid(db_unit.getid())
        newunit = db_unit.convert(file_store.UnitClass)
        assert str(newunit) == str(file_unit)


@pytest.mark.django_db
def test_sync_target(project0_nongnu, af_tutorial_po):
    """Tests that target changes are properly sync'ed to disk."""
    db_unit = af_tutorial_po.units.first()
    db_unit.target = u'samaka'
    db_unit.save()
    file_store, file_unit = _sync_translations(db_unit)
    assert (
        db_unit.target
        == file_unit.target
        == u'samaka')


@pytest.mark.django_db
def test_empty_plural_target(af_tutorial_po):
    """Tests empty plural targets are not deleted."""
    db_unit = af_tutorial_po.units.get(unitid="%d fish")
    db_unit.target = ["samaka"]
    db_unit.save()
    file_store, file_unit = _sync_translations(db_unit)
    assert file_unit.target == "samaka"
    assert len(file_unit.target.strings) == 2
    db_unit.refresh_from_db()
    db_unit.target = ""
    db_unit.save()
    file_store, file_unit = _sync_translations(db_unit)
    assert file_unit.target == ""
    assert len(file_unit.target.strings) == 2


@pytest.mark.django_db
def test_sync_plural_target(af_tutorial_po):
    """Tests plural translations are stored and sync'ed."""
    db_unit = af_tutorial_po.units.get(unitid="%d fish")
    db_unit.target = [u'samaka', u'samak']
    db_unit.save()
    file_store, file_unit = _sync_translations(db_unit)
    assert (
        db_unit.target.strings
        == file_unit.target.strings
        == [u'samaka', u'samak']
        == file_store.units[db_unit.index].target.strings)
    assert (
        db_unit.target
        == file_unit.target
        == u'samaka'
        == file_store.units[db_unit.index].target)


@pytest.mark.django_db
def test_sync_plural_target_dict(af_tutorial_po):
    """Tests plural translations are stored and sync'ed (dict version)."""
    db_unit = af_tutorial_po.units.get(unitid="%d fish")
    db_unit.target = {0: u'samaka', 1: u'samak'}
    db_unit.save()
    file_store, file_unit = _sync_translations(db_unit)
    assert (
        db_unit.target.strings
        == file_unit.target.strings
        == [u'samaka', u'samak']
        == file_store.units[db_unit.index].target.strings)
    assert (
        db_unit.target
        == file_unit.target
        == u'samaka'
        == file_store.units[db_unit.index].target)


@pytest.mark.django_db
def test_sync_fuzzy(project0_nongnu, af_tutorial_po):
    """Tests fuzzy state changes are stored and sync'ed."""
    db_unit = af_tutorial_po.units.first()
    db_unit.target = u'samaka'
    db_unit.markfuzzy()
    db_unit.save()
    file_store, file_unit = _sync_translations(db_unit)
    assert (
        db_unit.isfuzzy()
        == file_unit.isfuzzy()
        is True)
    db_unit.refresh_from_db()
    db_unit.markfuzzy(False)
    db_unit.save()
    file_store, file_unit = _sync_translations(db_unit)
    assert (
        db_unit.isfuzzy()
        == file_unit.isfuzzy()
        is False)


@pytest.mark.django_db
def test_sync_comment(project0_nongnu, af_tutorial_po):
    """Tests translator comments are stored and sync'ed."""
    db_unit = af_tutorial_po.units.first()
    db_unit.translator_comment = u'7amada'
    db_unit.save()
    file_store, file_unit = _sync_translations(db_unit)
    assert (
        db_unit.getnotes(origin='translator')
        == file_unit.getnotes(origin='translator')
        == u'7amada')


@pytest.mark.django_db
def test_add_suggestion(store0, system):
    """Tests adding new suggestions to units."""
    untranslated_unit = store0.units.filter(state=UNTRANSLATED)[0]
    translated_unit = store0.units.filter(state=TRANSLATED)[0]
    suggestion_text = 'foo bar baz'

    initial_suggestions = len(untranslated_unit.get_suggestions())
    suggestions = review.get(Suggestion)()

    # Empty suggestion is not recorded
    sugg, added = suggestions.add(untranslated_unit, "")
    assert sugg is None
    assert not added

    # Existing translation can't be added as a suggestion
    sugg, added = suggestions.add(translated_unit, translated_unit.target)
    assert sugg is None
    assert not added

    # Add new suggestion
    sugg, added = suggestions.add(untranslated_unit, suggestion_text)
    assert sugg is not None
    assert added
    assert len(untranslated_unit.get_suggestions()) == initial_suggestions + 1

    # Already-suggested text can't be suggested again
    assert suggestions.add(untranslated_unit, suggestion_text) == (None, False)
    assert len(untranslated_unit.get_suggestions()) == initial_suggestions + 1

    # Removing a suggestion should allow suggesting the same text again
    review.get(Suggestion)([sugg], system).reject()
    assert len(untranslated_unit.get_suggestions()) == initial_suggestions

    sugg, added = suggestions.add(untranslated_unit, suggestion_text)
    assert sugg is not None
    assert added
    assert len(untranslated_unit.get_suggestions()) == initial_suggestions + 1


@pytest.mark.django_db
def test_accept_suggestion_changes_state(issue_2401_po, system):
    """Tests that accepting a suggestion will change the state of the unit."""
    suggestions = review.get(Suggestion)()

    # First test with an untranslated unit
    unit = issue_2401_po.units[0]
    assert unit.state == UNTRANSLATED

    suggestion, created_ = suggestions.add(unit, "foo")
    assert unit.state == UNTRANSLATED

    review.get(Suggestion)([suggestion], system).accept()
    assert unit.state == TRANSLATED

    # Let's try with a translated unit now
    unit = issue_2401_po.units[1]
    assert unit.state == TRANSLATED

    suggestion, created_ = suggestions.add(unit, "bar")
    assert unit.state == TRANSLATED

    review.get(Suggestion)([suggestion], system).accept()
    assert unit.state == TRANSLATED

    # And finally a fuzzy unit
    unit = issue_2401_po.units[2]
    assert unit.state == FUZZY

    suggestion, created_ = suggestions.add(unit, "baz")
    assert unit.state == FUZZY

    review.get(Suggestion)([suggestion], system).accept()
    assert unit.state == TRANSLATED


@pytest.mark.django_db
def test_accept_suggestion_update_wordcount(it_tutorial_po, system):
    """Tests that accepting a suggestion for an untranslated unit will
    change the wordcount stats of the unit's store.
    """
    orig_translated = it_tutorial_po.data.translated_words
    suggestions = review.get(Suggestion)()
    untranslated_unit = it_tutorial_po.units[0]
    suggestion_text = 'foo bar baz'
    sugg, added = suggestions.add(untranslated_unit, suggestion_text)
    assert sugg is not None
    assert added
    assert len(untranslated_unit.get_suggestions()) == 1
    assert untranslated_unit.state == UNTRANSLATED
    review.get(Suggestion)([sugg], system).accept()
    assert untranslated_unit.state == TRANSLATED
    assert it_tutorial_po.data.translated_words > orig_translated


@pytest.mark.django_db
def test_unit_repr():
    unit = Unit.objects.first()
    assert str(unit) == str(unit.convert())
    assert unicode(unit) == unicode(unit.source)


@pytest.mark.django_db
def test_unit_po_plurals(store_po):
    unit = Unit(store=store_po)
    unit_po = pounit('bar')
    unit_po.msgid_plural = ['bars']
    unit.update(unit_po)
    assert unit.hasplural()
    unit.save()
    assert unit.hasplural()


@pytest.mark.django_db
def test_unit_ts_plurals(store_po, test_fs):
    with test_fs.open(['data', 'ts', 'add_plurals.ts']) as f:
        file_store = getclass(f)(f.read())
    unit = Unit(store=store_po)
    unit_ts = file_store.units[0]
    unit.update(unit_ts)
    assert unit.hasplural()
    unit.save()
    unit = Unit.objects.get(id=unit.id)
    assert unit.hasplural()
    unit.save()
    unit = Unit.objects.get(id=unit.id)
    assert unit.hasplural()


def _test_unit_syncer(unit, newunit):
    assert newunit.source == unit.source
    assert newunit.target == unit.target
    assert newunit.getid() == unit.getid()
    assert newunit.istranslated() == unit.istranslated()
    assert (
        newunit.getnotes(origin="developer")
        == unit.getnotes(origin="developer"))
    assert (
        newunit.getnotes(origin="translator")
        == unit.getnotes(origin="translator"))
    assert newunit.isobsolete() == unit.isobsolete()
    assert newunit.isfuzzy() == unit.isfuzzy()


@pytest.mark.django_db
def test_unit_syncer(unit_syncer):
    unit, unit_class = unit_syncer
    syncer = UnitSyncer(unit)
    newunit = syncer.convert(unit_class)
    assert newunit.istranslated()
    assert not newunit.isfuzzy()
    assert not newunit.isobsolete()
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_unit_syncer_fuzzy(unit_syncer):
    unit, unit_class = unit_syncer
    syncer = UnitSyncer(unit)
    unit.state = FUZZY
    unit.save()
    newunit = syncer.convert(unit_class)
    assert newunit.isfuzzy()
    assert not newunit.isobsolete()
    assert not newunit.istranslated()
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_unit_syncer_untranslated(unit_syncer):
    unit, unit_class = unit_syncer
    syncer = UnitSyncer(unit)
    unit.state = UNTRANSLATED
    unit.target = ""
    unit.save()
    newunit = syncer.convert(unit_class)
    assert not newunit.isfuzzy()
    assert not newunit.isobsolete()
    assert not newunit.istranslated()
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_unit_syncer_obsolete(unit_syncer):
    unit, unit_class = unit_syncer
    syncer = UnitSyncer(unit)
    unit.state = OBSOLETE
    unit.save()
    newunit = syncer.convert(unit_class)
    assert newunit.isobsolete()
    assert not newunit.isfuzzy()
    assert not newunit.istranslated()
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_unit_syncer_notes(unit_syncer):
    unit, unit_class = unit_syncer
    syncer = UnitSyncer(unit)
    unit.addnote(origin="developer", text="hello")
    newunit = syncer.convert(unit_class)
    assert newunit.getnotes(origin="developer") == "hello"
    _test_unit_syncer(unit, newunit)

    unit.addnote(origin="translator", text="world")
    newunit = syncer.convert(unit_class)
    assert newunit.getnotes(origin="translator") == "world"
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_unit_syncer_locations(unit_syncer):
    unit, unit_class = unit_syncer
    unit.addlocation("FOO")
    syncer = UnitSyncer(unit)
    newunit = syncer.convert(unit_class)
    assert newunit.getlocations() == ["FOO"]
    _test_unit_syncer(unit, newunit)


@pytest.mark.django_db
def test_add_autotranslated_unit(settings, store0, admin, no_wordcount):

    class DummyWordcount(object):

        def count(self, value):
            return counter(value) - value.count('Pootle')

        def count_words(self, strings):
            return sum(self.count(string) for string in strings)

    wc = DummyWordcount()

    with no_wordcount():

        @getter(wordcount, sender=Unit)
        def temp_wc_getter(**kwargs_):
            return wc

        unit = store0.addunit(
            store0.UnitClass(source_f='Pootle Pootle'),
            user=admin)

    dbunit = store0.units.get(id=unit.id)
    assert dbunit.state == FUZZY
    assert dbunit.target_f == unit.source_f

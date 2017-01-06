# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re

import pytest

from pootle.core.delegate import stemmer, terminology
from pootle_terminology.utils import UnitTerminology


@pytest.mark.django_db
def test_unit_terminology_instance(terminology_units, terminology0):
    unit = terminology0.stores.first().units.get(
        source_f=terminology_units)
    term = terminology.get(unit.__class__)(unit)
    assert isinstance(term, UnitTerminology)
    assert term.context == unit
    assert term.stop_words == []
    assert term.stemmer == stemmer.get()
    assert term.text == unit.source_f
    assert (
        term.split(term.text)
        == re.split(u"[\W]+", term.text))
    assert (
        term.tokens
        == [t.lower()
            for t
            in term.split(term.text)
            if (len(t) > 2
                and t not in term.stop_words)])
    assert (
        term.stems
        == set(term.stemmer(t) for t in term.tokens))
    assert term.stem_set == unit.stems
    assert term.stem_model == term.stem_set.model
    assert term.stem_m2m == term.stem_set.through
    unit.stems.all().delete()
    assert term.existing_stems == []
    term.stem()
    assert sorted(term.existing_stems) == sorted(term.stems)
    old_source = unit.source_f
    old_stems = term.existing_stems
    unit.source_f = "hatstand hatstand umbrella"
    unit.save()
    term.stem()
    assert (
        term.existing_stems
        == [u'hatstand', u'umbrella'])
    unit.source_f = old_source
    unit.save()
    term.stem()
    assert (
        term.existing_stems
        == old_stems)


@pytest.mark.django_db
def test_unit_terminology_bad(store0):
    unit = store0.units.first()
    with pytest.raises(ValueError):
        terminology.get(unit.__class__)(unit)

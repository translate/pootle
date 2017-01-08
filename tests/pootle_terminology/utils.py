# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re

import pytest

from pootle.core.delegate import (
    stemmer, stopwords, terminology, terminology_matcher)
from pootle_terminology.utils import UnitTerminology


@pytest.mark.django_db
def test_unit_terminology_instance(terminology_units, terminology0):
    units = terminology0.stores.first().units.filter(
        source_f=terminology_units)
    unit = None
    for _unit in units:
        if _unit.source_f == terminology_units:
            unit = _unit
            break
    term = terminology.get(unit.__class__)(unit)
    assert isinstance(term, UnitTerminology)
    assert term.context == unit
    assert term.stopwords == stopwords.get().words
    assert term.stemmer == stemmer.get()
    assert term.text == unit.source_f
    assert (
        term.split(term.text)
        == re.split(u"[^\w'-]+", term.text))
    assert (
        term.tokens
        == [t.lower()
            for t
            in term.split(term.text)
            if (len(t) > 2
                and t.lower() not in term.stopwords)])
    assert (
        term.stems
        == set(term.stemmer(t) for t in term.tokens))
    assert term.stem_set == unit.stems
    assert term.stem_model == term.stem_set.model
    assert term.stem_m2m == term.stem_set.through
    unit.stems.all().delete()
    assert term.existing_stems == set([])
    term.stem()
    assert sorted(term.existing_stems) == sorted(term.stems)
    old_source = unit.source_f
    old_stems = term.existing_stems
    unit.source_f = "hatstand hatstand umbrella"
    unit.save()
    term.stem()
    assert (
        sorted(term.existing_stems)
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


@pytest.mark.django_db
def test_terminology_matcher(store0, terminology0):

    for store in terminology0.stores.all():
        for unit in store.units.all():
            terminology.get(unit.__class__)(unit).stem()

    unit = store0.units.first()
    matcher = terminology_matcher.get(unit.__class__)(unit)
    assert matcher.text == unit.source_f
    assert (
        matcher.split(matcher.text)
        == re.split(u"[\W]+", matcher.text))
    assert (
        matcher.tokens
        == [t.lower()
            for t
            in matcher.split(matcher.text)
            if (len(t) > 2
                and t not in matcher.stopwords)])
    assert matcher.stems == set(matcher.stemmer(t) for t in matcher.tokens)
    assert (
        matcher.matches
        == matcher.similar(
            matcher.terminology_units.filter(
                stems__root__in=matcher.stems).distinct()))
    unit.source_f = "on the cycle home"
    unit.save()
    matches = []
    matched = []
    results = matcher.terminology_units.filter(
        stems__root__in=matcher.stems).distinct()
    for result in results:
        target_pair = (
            result.source_f.lower().strip(),
            result.target_f.lower().strip())
        if target_pair in matched:
            continue
        similarity = matcher.comparison.similarity(result.source_f)
        if similarity > matcher.similarity_threshold:
            matches.append((similarity, result))
            matched.append(target_pair)
    assert (
        matcher.similar(results)
        == sorted(matches, key=lambda x: -x[0])[:matcher.max_matches])
    assert (
        matcher.matches
        == matcher.similar(results))

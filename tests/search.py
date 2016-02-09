# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_store.models import Unit
from pootle_store.unit.filters import UnitTextSearch


def _expected_text_search_words(text, exact):
    if exact:
        return [text]
    return [t.strip() for t in text.split(" ") if t.strip()]


def _expected_text_search_results(qs, words, search_fields):

    def _search_field(k):
        subresult = qs.all()
        for word in words:
            subresult = subresult.filter(
                **{("%s__icontains" % k): word})
        return subresult

    result = qs.none()

    for k in search_fields:
        result = result | _search_field(k)
    return list(result.order_by("pk"))


def _expected_text_search_fields(sfields):
    search_fields = set()
    for field in sfields:
        if field in UnitTextSearch.search_mappings:
            search_fields.update(UnitTextSearch.search_mappings[field])
        else:
            search_fields.add(field)
    return search_fields


def _test_unit_text_search(qs, text, sfields, exact, empty=True):

    unit_search = UnitTextSearch(qs)
    result = unit_search.search(text, sfields, exact).order_by("pk")
    words = unit_search.get_words(text, exact)
    fields = unit_search.get_search_fields(sfields)

    # ensure result meets our expectation
    assert (
        list(result)
        == _expected_text_search_results(qs, words, fields))

    # ensure that there are no dupes in result qs
    assert list(result) == list(result.distinct())

    if not empty:
        assert result.count()

    for item in result:
        # item is in original qs
        assert item in qs

        for word in words:
            searchword_found = False
            for field in fields:
                if word.lower() in getattr(item, field).lower():
                    # one of the items attrs matches search
                    searchword_found = True
                    break
            assert searchword_found


@pytest.mark.django_db
def test_get_units_text_search(units_text_searches):
    search = units_text_searches

    sfields = search["sfields"]
    fields = _expected_text_search_fields(sfields)
    words = _expected_text_search_words(search['text'], search["exact"])

    # ensure the fields parser works correctly
    assert (
        UnitTextSearch(Unit.objects.all()).get_search_fields(sfields)
        == fields)
    # ensure the text tokeniser works correctly
    assert (
        UnitTextSearch(Unit.objects.all()).get_words(
            search['text'], search["exact"])
        == words)
    assert isinstance(words, list)

    # run the all units test first and check its not empty if it shouldnt be
    _test_unit_text_search(
        Unit.objects.all(),
        search["text"], search["sfields"], search["exact"],
        search["empty"])

    for qs in [Unit.objects.none(), Unit.objects.live()]:
        # run tests against different qs
        _test_unit_text_search(
            qs, search["text"], search["sfields"], search["exact"])

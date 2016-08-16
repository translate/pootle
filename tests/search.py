# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import search_backend
from pootle.core.plugin import getter
from pootle_project.models import Project
from pootle_statistics.models import SubmissionTypes
from pootle_store.getters import get_search_backend
from pootle_store.constants import FUZZY, TRANSLATED, UNTRANSLATED
from pootle_store.models import Unit
from pootle_store.util import SuggestionStates
from pootle_store.unit.filters import (
    FilterNotFound, UnitChecksFilter, UnitContributionFilter, UnitSearchFilter,
    UnitStateFilter, UnitTextSearch)
from pootle_store.unit.search import DBSearchBackend


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


def _test_units_checks_filter(qs, check_type, check_data):
    result = UnitChecksFilter(qs, **{check_type: check_data}).filter("checks")
    for item in result:
        assert item in qs
    assert result.count() == result.distinct().count()

    if check_type == "checks":
        for item in result:
            assert any(
                qc in item.qualitycheck_set.values_list("name", flat=True)
                for qc
                in check_data)
        assert(
            list(result)
            == list(
                qs.filter(
                    qualitycheck__false_positive=False,
                    qualitycheck__name__in=check_data).distinct()))
    else:
        for item in result:
            item.qualitycheck_set.values_list("category", flat=True)
        assert(
            list(result)
            == list(
                qs.filter(
                    qualitycheck__false_positive=False,
                    qualitycheck__category=check_data).distinct()))


def _test_units_contribution_filter(qs, user, unit_filter):
    result = UnitContributionFilter(qs, user=user).filter(unit_filter)
    for item in result:
        assert item in qs
    assert result.count() == result.distinct().count()
    user_subs_overwritten = [
        "my_submissions_overwritten",
        "user_submissions_overwritten"]
    if unit_filter == "suggestions":
        assert (
            result.count()
            == qs.filter(
                suggestion__state=SuggestionStates.PENDING).distinct().count())
        return
    elif not user:
        assert result.count() == 0
        return
    elif unit_filter in ["my_suggestions", "user_suggestions"]:
        expected = qs.filter(
            suggestion__state=SuggestionStates.PENDING,
            suggestion__user=user).distinct()
    elif unit_filter == "user_suggestions_accepted":
        expected = qs.filter(
            suggestion__state=SuggestionStates.ACCEPTED,
            suggestion__user=user).distinct()
    elif unit_filter == "user_suggestions_rejected":
        expected = qs.filter(
            suggestion__state=SuggestionStates.REJECTED,
            suggestion__user=user).distinct()
    elif unit_filter in ["my_submissions", "user_submissions"]:
        expected = qs.filter(
            submission__submitter=user,
            submission__type__in=SubmissionTypes.EDIT_TYPES).distinct()
    elif unit_filter in user_subs_overwritten:
        expected = qs.filter(
            submission__submitter=user,
            submission__type__in=SubmissionTypes.EDIT_TYPES)
        expected = expected.exclude(submitted_by=user).distinct()
    assert (
        list(expected.order_by("pk"))
        == list(result.order_by("pk")))


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


def _test_units_state_filter(qs, unit_filter):
    result = UnitStateFilter(qs).filter(unit_filter)
    for item in result:
        assert item in qs
    assert result.count() == result.distinct().count()
    if unit_filter == "all":
        assert list(result) == list(qs)
        return
    elif unit_filter == "translated":
        states = [TRANSLATED]
    elif unit_filter == "untranslated":
        states = [UNTRANSLATED]
    elif unit_filter == "fuzzy":
        states = [FUZZY]
    elif unit_filter == "incomplete":
        states = [UNTRANSLATED, FUZZY]
    assert all(
        state in states
        for state
        in result.values_list("state", flat=True))
    assert (
        qs.filter(state__in=states).count()
        == result.count())


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


@pytest.mark.django_db
def test_units_contribution_filter_none(units_contributor_searches):
    unit_filter = units_contributor_searches
    user = None

    qs = Unit.objects.all()
    if not hasattr(UnitContributionFilter, "filter_%s" % unit_filter):
        with pytest.raises(FilterNotFound):
            UnitContributionFilter(qs, user=user).filter(unit_filter)
        return
    test_qs = [
        qs,
        qs.none(),
        qs.filter(
            store__translation_project__project=Project.objects.first())]
    for _qs in test_qs:
        _test_units_contribution_filter(_qs, user, unit_filter)


@pytest.mark.django_db
def test_units_contribution_filter(units_contributor_searches, site_users):
    unit_filter = units_contributor_searches
    user = site_users["user"]

    qs = Unit.objects.all()
    if not hasattr(UnitContributionFilter, "filter_%s" % unit_filter):
        with pytest.raises(FilterNotFound):
            UnitContributionFilter(qs, user=user).filter(unit_filter)
        return
    test_qs = [
        qs,
        qs.none(),
        qs.filter(
            store__translation_project__project=Project.objects.first())]
    for _qs in test_qs:
        _test_units_contribution_filter(_qs, user, unit_filter)


@pytest.mark.django_db
def test_units_state_filter(units_state_searches):
    unit_filter = units_state_searches
    qs = Unit.objects.all()
    if not hasattr(UnitStateFilter, "filter_%s" % unit_filter):
        with pytest.raises(FilterNotFound):
            UnitStateFilter(qs).filter(unit_filter)
        return
    test_qs = [
        qs,
        qs.none(),
        qs.filter(
            store__translation_project__project=Project.objects.first())]
    for _qs in test_qs:
        _test_units_state_filter(_qs, unit_filter)


@pytest.mark.django_db
def test_units_checks_filter(units_checks_searches):
    check_type, check_data = units_checks_searches
    qs = Unit.objects.all()
    test_qs = [
        qs,
        qs.none(),
        qs.filter(
            store__translation_project__project=Project.objects.first())]
    for _qs in test_qs:
        _test_units_checks_filter(_qs, check_type, check_data)


@pytest.mark.django_db
def test_units_checks_filter_bad():
    qs = Unit.objects.all()
    with pytest.raises(FilterNotFound):
        UnitChecksFilter(qs).filter("BAD")
    # if you dont supply check/category you get empty qs
    assert not UnitChecksFilter(qs).filter("checks").count()


@pytest.mark.django_db
def test_units_filters():
    qs = Unit.objects.all()
    assert UnitSearchFilter().filter(qs, "FOO").count() == 0


@pytest.mark.django_db
def test_unit_search_backend():
    assert search_backend.get() is None
    assert search_backend.get(Unit) is DBSearchBackend


@pytest.mark.django_db
def test_unit_search_backend_custom():

    class CustomSearchBackend(DBSearchBackend):
        pass

    # add a custom getter, simulating adding before pootle_store
    # in INSTALLED_APPS

    # disconnect the default search_backend
    search_backend.disconnect(get_search_backend, sender=Unit)

    @getter(search_backend, sender=Unit)
    def custom_get_search_backend(**kwargs):
        return CustomSearchBackend

    # reconnect the default search_backend
    search_backend.connect(get_search_backend, sender=Unit)

    assert search_backend.get(Unit) is CustomSearchBackend

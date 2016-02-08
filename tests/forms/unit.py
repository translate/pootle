# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.db.models import Q

import pytest

import pytest

from pootle_app.models.permissions import get_matching_permissions
from pootle_statistics.models import SubmissionTypes
import pootle_store
from pootle_store.forms import unit_form_factory, UnitStateField
from pootle_store.models import Unit, SuggestionStates
from pootle_store.unit.filters import UnitTextSearch
from pootle_store.util import FUZZY, TRANSLATED, UNTRANSLATED


def _create_post_request(rf, directory, user, url='/', data=None):
    """Convenience function to create and setup fake POST requests."""
    if data is None:
        data = {}

    User = get_user_model()

    request = rf.post(url, data=data)
    request.user = user
    request.profile = User.get(user)
    request.permissions = get_matching_permissions(request.profile,
                                                   directory)
    return request


def _create_unit_form(request, language, unit):
    """Convenience function to create unit forms."""
    form_class = unit_form_factory(language, request=request)
    return form_class(request.POST, instance=unit, request=request)


@pytest.mark.django_db
def test_submit_no_source(rf, default, af_tutorial_po):
    """Tests that the source string cannot be modified."""
    language = af_tutorial_po.translation_project.language
    unit = af_tutorial_po.getitem(0)
    source_string = unit.source_f
    directory = unit.store.parent
    post_dict = {
        'id': unit.id,
        'index': unit.index,
        'source_f_0': 'altered source string',
        'target_f_0': 'dummy',
    }

    request = _create_post_request(rf, directory, data=post_dict, user=default)
    form = _create_unit_form(request, language, unit)

    assert form.is_valid()
    form.save()

    unit = af_tutorial_po.getitem(0)
    assert unit.source_f == source_string
    assert unit.target_f == 'dummy'


@pytest.mark.django_db
def test_submit_fuzzy(rf, admin, default,
                      afrikaans, af_tutorial_po):
    """Tests that non-admin users can't set the fuzzy flag."""
    language = afrikaans
    unit = af_tutorial_po.getitem(0)
    directory = unit.store.parent
    post_dict = {
        'id': unit.id,
        'index': unit.index,
        'target_f_0': unit.target_f,
        'state': FUZZY,
    }

    request = _create_post_request(rf, directory, data=post_dict, user=admin)
    admin_form = _create_unit_form(request, language, unit)
    assert admin_form.is_valid()

    request = _create_post_request(rf, directory, data=post_dict, user=default)
    user_form = _create_unit_form(request, language, unit)
    assert not user_form.is_valid()
    assert 'state' in user_form.errors


@pytest.mark.django_db
def test_submit_similarity(rf, default, afrikaans, af_tutorial_po):
    """Tests that similarities are within a particular range."""
    language = afrikaans
    unit = af_tutorial_po.getitem(0)
    directory = unit.store.parent

    post_dict = {
        'id': unit.id,
        'index': unit.index,
        'target_f_0': unit.target_f,
    }

    # Similarity should be optional
    request = _create_post_request(rf, directory, data=post_dict, user=default)
    form = _create_unit_form(request, language, unit)
    assert form.is_valid()

    # Similarities, if passed, should be in the [0..1] range
    post_dict.update({
        'similarity': 9999,
        'mt_similarity': 'foo bar',
    })
    request = _create_post_request(rf, directory, data=post_dict, user=default)
    form = _create_unit_form(request, language, unit)
    assert not form.is_valid()

    post_dict.update({
        'similarity': 1,
    })
    request = _create_post_request(rf, directory, data=post_dict, user=default)
    form = _create_unit_form(request, language, unit)
    assert not form.is_valid()

    post_dict.update({
        'mt_similarity': 2,
    })
    request = _create_post_request(rf, directory, data=post_dict, user=default)
    form = _create_unit_form(request, language, unit)
    assert not form.is_valid()

    post_dict.update({
        'mt_similarity': 0.69,
    })
    request = _create_post_request(rf, directory, data=post_dict, user=default)
    form = _create_unit_form(request, language, unit)
    assert form.is_valid()


def test_unit_state():
    """Tests how checkbox states (as strings) map to booleans."""
    field = UnitStateField(required=False)
    assert field.clean(str(FUZZY))
    assert field.clean(str(TRANSLATED))
    assert field.clean(str(UNTRANSLATED))
    assert field.clean(True)
    assert not field.clean('True')  # Unknown state value evaluates to False
    assert not field.clean(False)
    assert not field.clean('False')


def _calculate_results(form):

    pootle_path = form.cleaned_data["pootle_path"]
    qs = Unit.objects.get_for_path(pootle_path, form.request_user)
    search = form.cleaned_data["search"]
    sfields = form.cleaned_data["sfields"]
    search_exact = "exact" in form.cleaned_data["soptions"]

    # filter pootle path
    if pootle_path:
        qs = qs.filter(store__pootle_path__startswith=pootle_path)

    unit_filter = form.cleaned_data["filter"]

    # unit filter
    if unit_filter in ["translated", "untranslated", "fuzzy"]:
        qs = qs.filter(state=getattr(pootle_store.models, unit_filter.upper()))
    elif unit_filter == 'incomplete':
        qs = qs.filter(
            Q(state=pootle_store.models.UNTRANSLATED)
            | Q(state=pootle_store.models.FUZZY))
    elif unit_filter == 'suggestions':
        qs = qs.filter(suggestion__state=SuggestionStates.PENDING).distinct()
    elif unit_filter == 'user-suggestions':
        qs = qs.filter(
            suggestion__state=SuggestionStates.PENDING,
            suggestion__user=form.request_user)
    elif unit_filter == 'user-suggestions-accepted':
        qs = qs.filter(
            suggestion__state=SuggestionStates.ACCEPTED,
            suggestion__user=form.request_user)
    elif unit_filter == 'user-suggestions-rejected':
        qs = qs.filter(
            suggestion__state=SuggestionStates.REJECTED,
            suggestion__user=form.request_user)
    elif unit_filter == 'user-submissions':
        qs = qs.filter(
            submission__submitter=form.request_user,
            submission__type__in=SubmissionTypes.EDIT_TYPES)

    elif unit_filter == 'user-submissions-overwritten':
        qs = (
            qs.filter(submission__submitter=form.request_user,
                      submission__type__in=SubmissionTypes.EDIT_TYPES)
              .exclude(submitted_by=form.request_user)
              .distinct())

    if search and sfields:
        qs = UnitTextSearch(qs).search(search, sfields, search_exact)

    if form.cleaned_data.get("modified_since"):
        qs = qs.filter(mtime__gte=form.cleaned_data["modified_since"])

    if form.cleaned_data["uids"]:
        sort_by = form.cleaned_data.get("sort_by", None)
        if sort_by == "priority":
            qs = qs.distinct().order_by("priority")
        elif sort_by == "submitted_on":
            qs = qs.distinct().order_by("submitted_on")
        else:
            qs = qs.distinct().order_by("pk")

        found = False
        units = {}
        uids = []
        for unit in qs:
            if unit.pk == form.cleaned_data["uids"][0]:
                found = True
            if found:
                uids.append(unit.pk)
                units[unit.pk] = unit
    else:
        uids = qs.distinct().values_list("pk", flat=True)
        units = dict([(unit.pk, unit) for unit in qs.distinct()])

    return uids, units


def _test_form_filter(form, result):
    uids, expected = _calculate_results(form)
    unit_count = 0
    for group in result["unitGroups"]:
        for result_store, info in group.items():
            for result_unit in info['units']:
                uids[unit_count] == result_unit["id"]
                unit_count += 1
                unit = expected.get(result_unit["id"])
                assert result_unit['isfuzzy'] == unit.isfuzzy()
                # TODO: test rest of content of dict
    assert len(uids) == unit_count


def _test_form_sorting(form, result):
    # expected = _calculate_results(form)
    sort_units_oldest = (
        form.cleaned_data["sort_on"] == "units"
        and form.cleaned_data["sort_by_param"] == "oldest")
    if sort_units_oldest:
        pass
        # groups = result["unitGroups"]
        # the first unit in each group should be in correct order
        # units = []
        # for group in groups:
        #    units.append(group["units"][0])


@pytest.mark.django_db
def test_get_units_form(units_form_tests):
    (form, params, default, member, member2) = units_form_tests

    if params.get("valid", None) is False:
        assert not form.is_valid()
        # TODO: catch specific errors?
        return

    assert form.is_valid()

    if "user" not in params:
        params["cleaned_data"]["user"] = default

    params["cleaned_data"]['path'] = unicode(params["get"]["path"])

    # TODO: vfolders...
    params["cleaned_data"]['pootle_path'] = params["cleaned_data"]['path']

    if form.data.getlist("uids", None) is not None:
        params["cleaned_data"]["uids"] = [
            int(x) for x in form.data.getlist("uids")]

    limit = params["get"].pop("limit", False)

    assert form.cleaned_data == params["cleaned_data"]

    result = form.search_units(limit=limit)
    assert (
        result
        == form.unit_search_class(
            Unit.objects.get_for_path(
                params["cleaned_data"]['pootle_path'], form.request_user),
            request_user=form.request_user,
            limit=limit,
            **form.cleaned_data).grouped_search())


@pytest.mark.django_db
def test_get_units_filter(units_filter_tests):
    from pootle_store.unit.filters import UnitTextSearch

    (unit_filter, params, request_user, qs) = units_filter_tests
    cleaned = params["cleaned_data"]

    assert unit_filter.qs == qs
    assert unit_filter.filters == [
        "vfolder", "unit_filter", "checks", "mtime",
        "month", "text_search"]

    filtered_qs = qs.all()

    if cleaned.get("pootle_path", None):
        filtered_qs = filtered_qs.filter(
            store__pootle_path__startswith=cleaned["pootle_path"])

    if cleaned.get("vfolder", None):
        filtered_qs = filtered_qs.filter(
            vfolders=cleaned["vfolder"])

    if cleaned.get("filter", None):
        query_attr = "%s_q" % cleaned["filter"].replace("-", "_")
        query_method = getattr(unit_filter, query_attr, None)
        if query_method is not None:
            filtered_qs = filtered_qs.filter(
                query_method(cleaned.get('user', request_user)))

    if cleaned.get("checks", None):
        checks = cleaned.get("checks", None)
        category = cleaned.get("category", None)
        if checks is not None:
            filtered_qs = filtered_qs.filter(
                qualitycheck__false_positive=False,
                qualitycheck__name__in=checks)
        elif category:
            filtered_qs = filtered_qs.filter(
                qualitycheck__false_positive=False,
                qualitycheck__category=category)

    if cleaned.get("modified_since", None):
        filtered_qs = filtered_qs.filter(
            submitted_on__gt=cleaned['modified_since'])

    if cleaned.get("month", None):
        [start, end] = cleaned['month']
        filtered_qs = filtered_qs.filter(
            submitted_on__gte=start,
            submitted_on__lte=end)

    if cleaned.get("search", None) and cleaned.get("sfields", None):
        filtered_qs = UnitTextSearch(filtered_qs).search(
            cleaned['search'],
            cleaned['sfields'],
            "exact" in cleaned.get("soptions", []))

    assert list(unit_filter.filter_qs(**cleaned)) == list(filtered_qs)


@pytest.mark.django_db
def test_get_units_search(units_search_tests):
    (search, params, request_user, limit, qs) = units_search_tests

    cleaned = params["cleaned_data"]
    if not cleaned.get("user", None):
        cleaned["user"] = request_user

    # the search instance has the qs attr
    assert list(search.qs) == list(qs)

    # filtered_qs is equiv to calling the the filter_class
    # with the qs and the kwa
    filtered_qs = search.filter_class(qs).filter_qs(**cleaned)
    assert list(search.filtered_qs) == list(filtered_qs)
    assert search.total == filtered_qs.count()

    # sorted_qs is equiv to calling the the sort_class
    # with the filtered_qs and the sort kwa
    sorted_qs = search.sort_class(filtered_qs).sort_qs(
        cleaned.get("sort_on"), cleaned.get("sort_by"))
    assert list(search.sorted_qs) == list(sorted_qs)

    # sort field and comparators
    if sorted_qs.query.order_by:
        assert search._order_by == sorted_qs.query.order_by[0]
        assert search.order_by == search._order_by.strip("-")
    else:
        assert search._order_by is None
        assert search.order_by == "pk"

    lte = (
        cleaned["sort_by"]
        and cleaned["sort_by"].startswith("-"))
    if lte:
        search.compare_with == "lte"
    else:
        search.compare_with == "gte"

    # result slicing
    start_index = 0
    next_uids = []
    previous_uids = []
    sliced_qs = sorted_qs.all()

    if search.order_by == "sort_by_field":
        uid_list = [x for x, y in sorted_qs.values_list("pk", "sort_by_field")]
    else:
        uid_list = list(sorted_qs.values_list("pk", flat=True))
    uids = cleaned["uids"]
    if uids:
        start_index = uid_list.index(uids[0])
        prev_start = start_index - 10
        if prev_start < 0:
            prev_start = 0
        previous_uids = uid_list[prev_start:start_index]

    sliced_qs = sliced_qs[start_index:]

    if limit:
        sliced_qs = sliced_qs[:limit]
        next_uids = sliced_qs[limit:limit + 10]

    assert list(search.sliced_qs) == list(sliced_qs)
    assert search.previous_uids == previous_uids
    assert search.next_uids == next_uids

    unit_groups = search.group_class(sliced_qs).group_units()
    for i, group in enumerate(unit_groups):
        assert search.unit_groups[i] == group

    grouped_search = search.grouped_search()
    assert grouped_search["total"] == search.total
    assert grouped_search["next_uids"] == search.next_uids
    assert grouped_search["previous_uids"] == search.previous_uids
    assert grouped_search["unitGroups"] == search.unit_groups

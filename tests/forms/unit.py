# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model

import pytest

from pootle_app.models.permissions import get_matching_permissions
from pootle_store.forms import unit_form_factory, UnitStateField
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

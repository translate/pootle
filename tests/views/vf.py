# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from pytest_pootle.search import calculate_search_results

from django.core.urlresolvers import resolve, reverse


@pytest.mark.django_db
def test_view_vf_tp_translate_reverse():
    # tp translate views
    tp_translate_view = reverse(
        "pootle-vfolder-tp-translate",
        kwargs=dict(
            vfolder_name="VF_NAME",
            language_code="LANG_CODE",
            project_code="PROJ_CODE"))
    assert (
        tp_translate_view
        == u'/++vfolder/VF_NAME/LANG_CODE/PROJ_CODE/translate/')
    tp_translate_subdir_view = reverse(
        "pootle-vfolder-tp-translate",
        kwargs=dict(
            vfolder_name="VF_NAME",
            language_code="LANG_CODE",
            project_code="PROJ_CODE",
            dir_path="SOME/SUBDIR/"))
    assert (
        tp_translate_subdir_view
        == u'/++vfolder/VF_NAME/LANG_CODE/PROJ_CODE/translate/SOME/SUBDIR/')


@pytest.mark.django_db
def test_view_vf_xhr_units():
    xhr_units = reverse(
        "vfolder-pootle-xhr-units",
        kwargs=dict(vfolder_name="VF_NAME"))
    assert xhr_units == "/++vfolder/VF_NAME/xhr/units/"


@pytest.mark.django_db
def test_view_vf_xhr_units_resolve():
    assert (
        resolve("/++vfolder/VF_NAME/xhr/units/12345/edit").func.__name__
        == "UnitEditJSON")


@pytest.mark.django_db
def test_view_vf_xhr_edit_unit():
    xhr_units = reverse(
        "vfolder-pootle-xhr-units",
        kwargs=dict(vfolder_name="VF_NAME"))
    assert xhr_units == "/++vfolder/VF_NAME/xhr/units/"


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_views_vf_translate(vfolder_views, settings):
    from tp import _test_translate_view

    test_type, tp, request, response, kwargs = vfolder_views
    _test_translate_view(tp, request, response, kwargs, settings)


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_views_vf_get_units(get_vfolder_units_views):
    (user, vfolder, search_params,
     url_params, response) = get_vfolder_units_views
    result = json.loads(response.content)

    assert "unitGroups" in result
    assert isinstance(result["unitGroups"], list)

    for k in "start", "end", "total":
        assert k in result
        assert isinstance(result[k], int)

    search_params["vfolder"] = vfolder
    if result["unitGroups"]:
        total, start, end, expected_units = calculate_search_results(
            search_params, user)

        assert result["total"] == total
        assert result["start"] == start
        assert result["end"] == end

        for i, group in enumerate(expected_units):
            result_group = result["unitGroups"][i]
            for store, data in group.items():
                result_data = result_group[store]
                assert (
                    [u["id"] for u in result_data["units"]]
                    == [u["id"] for u in data["units"]])


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_views_vf_get_units_bad(request, client, vfolder0):

    response = client.get(
        reverse(
            "vfolder-pootle-xhr-units",
            kwargs=dict(vfolder_name="NO_SUCH_VFOLDER")),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 404

    # path not set
    response = client.get(
        reverse(
            "vfolder-pootle-xhr-units",
            kwargs=dict(vfolder_name=vfolder0.name)),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 400

    # path too long
    response = client.get(
        "%s?path=%s"
        % (reverse("vfolder-pootle-xhr-units",
                   kwargs=dict(vfolder_name=vfolder0.name)),
           ("x" * 3000)),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 400

    # unrecognized path
    response = client.get(
        "%s?path=%s"
        % (reverse("vfolder-pootle-xhr-units",
                   kwargs=dict(vfolder_name=vfolder0.name)),
           ("x" * 100)),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 404

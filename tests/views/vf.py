# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
from collections import OrderedDict

import pytest

from pytest_pootle.search import calculate_search_results

from django.urls import resolve, reverse

from pootle_app.models.permissions import check_permission
from pootle.core.url_helpers import get_previous_url, get_path_parts
from pootle_checks.constants import CATEGORY_IDS, CHECK_NAMES
from pootle_checks.utils import get_qualitychecks, get_qualitycheck_schema
from pootle_misc.forms import make_search_form
from virtualfolder.models import VirtualFolder
from virtualfolder.utils import DirectoryVFDataTool


def _test_vf_translate_view(tp, request, response, kwargs, settings):
    from .tp import view_context_test

    ctx = response.context
    obj = ctx["object"]
    kwargs["project_code"] = tp.project.code
    kwargs["language_code"] = tp.language.code
    resource_path = "%(dir_path)s%(filename)s" % kwargs
    request_path = "%s%s" % (tp.pootle_path, resource_path)

    checks = get_qualitychecks()
    schema = {sc["code"]: sc for sc in get_qualitycheck_schema()}
    vfolder_pk = response.context["current_vfolder_pk"]
    check_data = DirectoryVFDataTool(obj).get_checks(
        user=request.user).get(vfolder_pk, {})
    _checks = {}
    for check, checkid in checks.items():
        if check not in check_data:
            continue
        _checkid = schema[checkid]["name"]
        _checks[_checkid] = _checks.get(
            _checkid, dict(checks=[], title=schema[checkid]["title"]))
        _checks[_checkid]["checks"].append(
            dict(
                code=check,
                title=CHECK_NAMES[check],
                count=check_data[check]))
    _checks = OrderedDict(
        (k, _checks[k])
        for k in CATEGORY_IDS.keys()
        if _checks.get(k))
    vfolder = VirtualFolder.objects.get(
        name=request.resolver_match.kwargs["vfolder_name"])
    current_vfolder_pk = vfolder.pk
    display_priority = False
    unit_api_root = reverse(
        "vfolder-pootle-xhr-units",
        kwargs=dict(vfolder_name=vfolder.name))
    resource_path = (
        "/".join(
            ["++vfolder",
             vfolder.name,
             ctx['object'].pootle_path.replace(tp.pootle_path, "")]))
    assertions = dict(
        page="translate",
        translation_project=tp,
        language=tp.language,
        project=tp.project,
        has_admin_access=check_permission('administrate', request),
        ctx_path=tp.pootle_path,
        pootle_path=request_path,
        resource_path=resource_path,
        resource_path_parts=get_path_parts(resource_path),
        editor_extends="translation_projects/base.html",
        checks=_checks,
        previous_url=get_previous_url(request),
        current_vfolder_pk=current_vfolder_pk,
        display_priority=display_priority,
        cantranslate=check_permission("translate", request),
        cansuggest=check_permission("suggest", request),
        canreview=check_permission("review", request),
        search_form=make_search_form(request=request),
        unit_api_root=unit_api_root,
        POOTLE_MT_BACKENDS=settings.POOTLE_MT_BACKENDS,
        AMAGAMA_URL=settings.AMAGAMA_URL)
    view_context_test(ctx, **assertions)


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
    test_type, tp, request, response, kwargs = vfolder_views
    _test_vf_translate_view(tp, request, response, kwargs, settings)


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

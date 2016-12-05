# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
from collections import OrderedDict
from urllib import unquote

import pytest

from pytest_pootle.suite import view_context_test

from django.contrib.auth import get_user_model

from pootle_app.models import Directory
from pootle_app.models.permissions import check_permission
from pootle.core.browser import get_parent
from pootle.core.helpers import (
    SIDEBAR_COOKIE_NAME, get_sidebar_announcements_context)
from pootle.core.url_helpers import get_previous_url, get_path_parts
from pootle.core.utils.stats import (get_top_scorers_data,
                                     get_translation_states)
from pootle.core.views.display import ChecksDisplay
from pootle_misc.checks import (
    CATEGORY_IDS, check_names,
    get_qualitychecks, get_qualitycheck_schema)
from pootle.core.views.browse import StatsDisplay
from pootle_misc.forms import make_search_form
from pootle_store.models import Store
from virtualfolder.delegate import vfolders_data_view


def _test_browse_view(tp, request, response, kwargs):
    if SIDEBAR_COOKIE_NAME in response.cookies:
        cookie_data = json.loads(
            unquote(response.cookies[SIDEBAR_COOKIE_NAME].value))
        assert cookie_data["foo"] == "bar"
    assert "announcements/projects/%s" % tp.project.code in request.session
    assert "announcements/%s" % tp.language.code in request.session
    assert (
        "announcements/%s/%s"
        % (tp.language.code, tp.project.code)
        in request.session)
    ctx = response.context
    kwargs["project_code"] = tp.project.code
    kwargs["language_code"] = tp.language.code
    resource_path = "%(dir_path)s%(filename)s" % kwargs
    pootle_path = "%s%s" % (tp.pootle_path, resource_path)

    if not (kwargs["dir_path"] or kwargs.get("filename")):
        obj = tp.directory
    elif not kwargs.get("filename"):
        obj = Directory.objects.get(
            pootle_path=pootle_path)
    else:
        obj = Store.objects.get(
            pootle_path=pootle_path)
    if obj.tp_path == "/":
        data_obj = obj.tp
    else:
        data_obj = obj
    stats = StatsDisplay(
        data_obj,
        stats=data_obj.data_tool.get_stats(user=request.user)).stats
    if not kwargs.get("filename"):
        vfolders = True
    else:
        vfolders = None
    filters = {}
    if vfolders:
        filters['sort'] = 'priority'
    checks = ChecksDisplay(obj).checks_by_category
    del stats["children"]

    User = get_user_model()
    top_scorers = User.top_scorers(language=tp.language.code,
                                   project=tp.project.code, limit=11)
    assertions = dict(
        page="browse",
        object=obj,
        translation_project=tp,
        language=tp.language,
        project=tp.project,
        has_admin_access=check_permission('administrate', request),
        is_store=(kwargs.get("filename") and True or False),
        browser_extends="translation_projects/base.html",
        pootle_path=pootle_path,
        resource_path=resource_path,
        resource_path_parts=get_path_parts(resource_path),
        translation_states=get_translation_states(obj),
        checks=checks,
        top_scorers=top_scorers,
        top_scorers_data=get_top_scorers_data(top_scorers, 10),
        url_action_continue=obj.get_translate_url(
            state='incomplete', **filters),
        url_action_fixcritical=obj.get_critical_url(**filters),
        url_action_review=obj.get_translate_url(
            state='suggestions', **filters),
        url_action_view_all=obj.get_translate_url(state='all'),
        stats=stats,
        parent=get_parent(obj))
    sidebar = get_sidebar_announcements_context(
        request, (tp.project, tp.language, tp))
    for k in ["has_sidebar", "is_sidebar_open", "announcements"]:
        assertions[k] = sidebar[0][k]
    view_context_test(ctx, **assertions)
    assert (('display_download' in ctx and ctx['display_download']) ==
            (request.user.is_authenticated
             and check_permission('translate', request)))


def _test_translate_view(tp, request, response, kwargs, settings):
    ctx = response.context
    obj = ctx["object"]
    kwargs["project_code"] = tp.project.code
    kwargs["language_code"] = tp.language.code
    resource_path = "%(dir_path)s%(filename)s" % kwargs
    request_path = "%s%s" % (tp.pootle_path, resource_path)

    checks = get_qualitychecks()
    schema = {sc["code"]: sc for sc in get_qualitycheck_schema()}
    check_data = obj.data_tool.get_checks()
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
                title=check_names[check],
                count=check_data[check]))
    _checks = OrderedDict(
        (k, _checks[k])
        for k in CATEGORY_IDS.keys()
        if _checks.get(k))
    current_vfolder_pk = ""
    display_priority = False
    if not kwargs["filename"]:
        vf_view = vfolders_data_view.get(obj.__class__)(obj, request.user)
        display_priority = vf_view.has_data
    unit_api_root = "/xhr/units/"
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


@pytest.mark.pootle_vfolders
@pytest.mark.django_db
def test_views_tp(tp_views, settings):
    test_type, tp, request, response, kwargs = tp_views
    if test_type == "browse":
        _test_browse_view(tp, request, response, kwargs)
    elif test_type == "translate":
        _test_translate_view(tp, request, response, kwargs, settings)


@pytest.mark.django_db
def test_view_user_choice(client):

    client.cookies["user-choice"] = "language"
    response = client.get("/foo/bar/baz")
    assert response.status_code == 302
    assert response.get("location") == "/foo/"
    assert "user-choice" not in response

    client.cookies["user-choice"] = "project"
    response = client.get("/foo/bar/baz")
    assert response.status_code == 302
    assert response.get("location") == "/projects/bar/"
    assert "user-choice" not in response

    client.cookies["user-choice"] = "foo"
    response = client.get("/foo/bar/baz")
    assert response.status_code == 404
    assert "user-choice" not in response


@pytest.mark.django_db
def test_uploads_tp(revision, tp_uploads):
    tp_, request_, response, kwargs_, errors = tp_uploads
    assert response.status_code == 200
    assert errors.keys() == response.context['upload_form'].errors.keys()

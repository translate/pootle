# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest

from django.urls import reverse

from pytest_pootle.suite import view_context_test

from pootle_app.models import Directory
from pootle_app.models.permissions import check_permission
from pootle.core.delegate import scores
from pootle.core.helpers import get_sidebar_announcements_context
from pootle.core.url_helpers import get_previous_url, get_path_parts
from pootle.core.utils.stats import (
    TOP_CONTRIBUTORS_CHUNK_SIZE, get_translation_states)
from pootle.core.views.display import ChecksDisplay
from pootle.core.views.browse import StatsDisplay
from pootle_checks.constants import CATEGORY_IDS, CHECK_NAMES
from pootle_checks.utils import get_qualitychecks, get_qualitycheck_schema
from pootle_misc.forms import make_search_form
from pootle_project.models import Project, ProjectResource, ProjectSet
from pootle_store.models import Store


def _test_translate_view(project, request, response, kwargs, settings):

    if not request.user.is_superuser:
        assert response.status_code == 403
        return

    ctx = response.context
    kwargs["project_code"] = project.code
    ctx_path = (
        "/projects/%(project_code)s/" % kwargs)
    resource_path = (
        "%(dir_path)s%(filename)s" % kwargs)
    pootle_path = "%s%s" % (ctx_path, resource_path)
    display_priority = False

    checks = get_qualitychecks()
    schema = {sc["code"]: sc for sc in get_qualitycheck_schema()}
    check_data = ctx["object"].data_tool.get_checks()
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
    view_context_test(
        ctx,
        **dict(
            page="translate",
            has_admin_access=request.user.is_superuser,
            language=None,
            project=project,
            pootle_path=pootle_path,
            ctx_path=ctx_path,
            resource_path=resource_path,
            resource_path_parts=get_path_parts(resource_path),
            editor_extends="projects/base.html",
            checks=_checks,
            previous_url=get_previous_url(request),
            display_priority=display_priority,
            cantranslate=check_permission("translate", request),
            cansuggest=check_permission("suggest", request),
            canreview=check_permission("review", request),
            search_form=make_search_form(request=request),
            current_vfolder_pk="",
            POOTLE_MT_BACKENDS=settings.POOTLE_MT_BACKENDS,
            AMAGAMA_URL=settings.AMAGAMA_URL))


def _test_browse_view(project, request, response, kwargs):
    assert (request.user.is_anonymous
            or "announcements/projects/%s" % project.code in request.session)
    ctx = response.context
    kwargs["project_code"] = project.code
    resource_path = (
        "%(dir_path)s%(filename)s" % kwargs)
    project_path = (
        "%s/%s"
        % (kwargs["project_code"], resource_path))
    if not (kwargs["dir_path"] or kwargs["filename"]):
        obj = project
    elif not kwargs["filename"]:
        obj = ProjectResource(
            Directory.objects.live().filter(
                pootle_path__regex="^/.*/%s$" % project_path),
            pootle_path="/projects/%s" % project_path)
    else:
        obj = ProjectResource(
            Store.objects.live().filter(
                pootle_path__regex="^/.*/%s$" % project_path),
            pootle_path="/projects/%s" % project_path)

    stats = obj.data_tool.get_stats(user=request.user)

    if request.user.is_superuser or kwargs.get("language_code"):
        url_action_continue = obj.get_translate_url(state='incomplete')
        url_action_fixcritical = obj.get_critical_url()
        url_action_review = obj.get_translate_url(state='suggestions')
        url_action_view_all = obj.get_translate_url(state='all')
    else:
        (url_action_continue,
         url_action_fixcritical,
         url_action_review,
         url_action_view_all) = [None] * 4
    checks = ChecksDisplay(obj).checks_by_category
    stats = StatsDisplay(obj, stats=stats).stats
    del stats["children"]

    chunk_size = TOP_CONTRIBUTORS_CHUNK_SIZE
    score_data = scores.get(Project)(project)

    def scores_to_json(score):
        score["user"] = score["user"].to_dict()
        return score
    top_scorers = score_data.display(
        limit=chunk_size,
        formatter=scores_to_json)
    top_scorer_data = dict(
        items=list(top_scorers),
        has_more_items=len(score_data.top_scorers) > chunk_size)
    assertions = dict(
        page="browse",
        project=project,
        browser_extends="projects/base.html",
        pootle_path="/projects/%s" % project_path,
        resource_path=resource_path,
        resource_path_parts=get_path_parts(resource_path),
        url_action_continue=url_action_continue,
        url_action_fixcritical=url_action_fixcritical,
        url_action_review=url_action_review,
        url_action_view_all=url_action_view_all,
        translation_states=get_translation_states(obj),
        top_scorers=top_scorer_data,
        checks=checks,
        stats=stats)
    sidebar = get_sidebar_announcements_context(
        request, (project, ))
    for k in ["has_sidebar", "is_sidebar_open", "announcements"]:
        assertions[k] = sidebar[k]
    view_context_test(ctx, **assertions)


@pytest.mark.django_db
def test_views_project(project_views, settings):
    test_type, project, request, response, kwargs = project_views
    if test_type == "browse":
        _test_browse_view(project, request, response, kwargs)
    elif test_type == "translate":
        _test_translate_view(project, request, response, kwargs, settings)


@pytest.mark.django_db
def test_view_projects_browse(client, request_users):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(reverse("pootle-projects-browse"))
    assert response.cookies["pootle-language"].value == "projects"
    ctx = response.context
    request = response.wsgi_request
    user_projects = Project.accessible_by_user(request.user)
    user_projects = (
        Project.objects.for_user(request.user)
                       .filter(code__in=user_projects))
    obj = ProjectSet(user_projects)
    stats = obj.data_tool.get_stats(user=request.user)

    if request.user.is_superuser:
        url_action_continue = obj.get_translate_url(state='incomplete')
        url_action_fixcritical = obj.get_critical_url()
        url_action_review = obj.get_translate_url(state='suggestions')
        url_action_view_all = obj.get_translate_url(state='all')
    else:
        (url_action_continue,
         url_action_fixcritical,
         url_action_review,
         url_action_view_all) = [None] * 4
    checks = ChecksDisplay(obj).checks_by_category
    stats = StatsDisplay(obj, stats=stats).stats
    del stats["children"]
    chunk_size = TOP_CONTRIBUTORS_CHUNK_SIZE
    score_data = scores.get(ProjectSet)(obj)

    def scores_to_json(score):
        score["user"] = score["user"].to_dict()
        return score
    top_scorers = score_data.display(
        limit=chunk_size,
        formatter=scores_to_json)
    top_scorer_data = dict(
        items=list(top_scorers),
        has_more_items=len(score_data.top_scorers) > chunk_size)
    assertions = dict(
        page="browse",
        pootle_path="/projects/",
        resource_path="",
        resource_path_parts=[],
        object=obj,
        browser_extends="projects/all/base.html",
        top_scorers=top_scorer_data,
        translation_states=get_translation_states(obj),
        url_action_continue=url_action_continue,
        url_action_fixcritical=url_action_fixcritical,
        url_action_review=url_action_review,
        url_action_view_all=url_action_view_all,
        checks=checks,
        stats=stats)
    view_context_test(ctx, **assertions)


@pytest.mark.django_db
def test_view_projects_translate(client, settings, request_users):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(reverse("pootle-projects-translate"))

    if not user.is_superuser:
        assert response.status_code == 403
        return
    ctx = response.context
    request = response.wsgi_request
    user_projects = Project.accessible_by_user(request.user)
    user_projects = (
        Project.objects.for_user(request.user)
                       .filter(code__in=user_projects))
    obj = ProjectSet(user_projects)
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
                title=CHECK_NAMES[check],
                count=check_data[check]))
    _checks = OrderedDict(
        (k, _checks[k])
        for k in CATEGORY_IDS.keys()
        if _checks.get(k))
    assertions = dict(
        page="translate",
        has_admin_access=user.is_superuser,
        language=None,
        project=None,
        pootle_path="/projects/",
        ctx_path="/projects/",
        resource_path="",
        resource_path_parts=[],
        editor_extends="projects/all/base.html",
        checks=_checks,
        previous_url=get_previous_url(request),
        display_priority=False,
        cantranslate=check_permission("translate", request),
        cansuggest=check_permission("suggest", request),
        canreview=check_permission("review", request),
        search_form=make_search_form(request=request),
        current_vfolder_pk="",
        POOTLE_MT_BACKENDS=settings.POOTLE_MT_BACKENDS,
        AMAGAMA_URL=settings.AMAGAMA_URL)
    view_context_test(ctx, **assertions)

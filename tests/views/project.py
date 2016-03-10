# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from itertools import groupby
import json
import locale
from urllib import unquote

import pytest

from django.core.urlresolvers import reverse

from pytest_pootle.suite import view_context_test

from pootle_app.models import Directory
from pootle_app.models.permissions import check_permission
from pootle.core.browser import (
    get_table_headings, make_language_item, make_xlanguage_item,
    make_project_list_item)
from pootle.core.helpers import (
    SIDEBAR_COOKIE_NAME,
    get_filter_name, get_sidebar_announcements_context)
from pootle.core.utils.json import jsonify
from pootle.core.url_helpers import get_previous_url, get_path_parts
from pootle_misc.checks import get_qualitycheck_schema
from pootle_misc.forms import make_search_form
from pootle_misc.stats import get_translation_states
from pootle_project.models import Project, ProjectResource, ProjectSet
from pootle_store.forms import UnitExportForm
from pootle_store.models import Store
from pootle_store.util import get_search_backend
from virtualfolder.models import VirtualFolderTreeItem


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
    view_context_test(
        ctx,
        **dict(
            page="translate",
            is_admin=request.user.is_superuser,
            language=None,
            project=project,
            pootle_path=pootle_path,
            ctx_path=ctx_path,
            resource_path=resource_path,
            resource_path_parts=get_path_parts(resource_path),
            editor_extends="projects/base.html",
            check_categories=get_qualitycheck_schema(),
            previous_url=get_previous_url(request),
            display_priority=(
                VirtualFolderTreeItem.objects.filter(
                    pootle_path__startswith=pootle_path).exists()),
            cantranslate=check_permission("translate", request),
            cansuggest=check_permission("suggest", request),
            canreview=check_permission("review", request),
            search_form=make_search_form(request=request),
            current_vfolder_pk="",
            POOTLE_MT_BACKENDS=settings.POOTLE_MT_BACKENDS,
            AMAGAMA_URL=settings.AMAGAMA_URL))


def _test_browse_view(project, request, response, kwargs):
    cookie_data = json.loads(
        unquote(response.cookies[SIDEBAR_COOKIE_NAME].value))
    assert cookie_data["foo"] == "bar"
    assert "announcements_projects_%s" % project.code in cookie_data
    ctx = response.context
    kwargs["project_code"] = project.code
    resource_path = (
        "%(dir_path)s%(filename)s" % kwargs)
    project_path = (
        "%s/%s"
        % (kwargs["project_code"], resource_path))
    if not (kwargs["dir_path"] or kwargs["filename"]):
        ob = project
    elif not kwargs["filename"]:
        ob = ProjectResource(
            Directory.objects.live().filter(
                pootle_path__regex="^/.*/%s$" % project_path),
            pootle_path="/projects/%s" % project_path)
    else:
        ob = ProjectResource(
            Store.objects.live().filter(
                pootle_path__regex="^/.*/%s$" % project_path),
            pootle_path="/projects/%s" % project_path)

    item_func = (
        make_xlanguage_item
        if (kwargs["dir_path"]
            or kwargs["filename"])
        else make_language_item)
    items = [
        item_func(item)
        for item
        in ob.get_children_for_user(request.user)
    ]
    items.sort(lambda x, y: locale.strcoll(x['title'], y['title']))

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'suggestions', 'critical', 'last-updated', 'activity']
    table = {
        'id': 'project',
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': items}

    if request.user.is_superuser or kwargs.get("language_code"):
        url_action_continue = ob.get_translate_url(state='incomplete')
        url_action_fixcritical = ob.get_critical_url()
        url_action_review = ob.get_translate_url(state='suggestions')
        url_action_view_all = ob.get_translate_url(state='all')
    else:
        (url_action_continue,
         url_action_fixcritical,
         url_action_review,
         url_action_view_all) = [None] * 4

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
        translation_states=get_translation_states(ob),
        check_categories=get_qualitycheck_schema(ob),
        table=table,
        stats=jsonify(ob.get_stats()))
    sidebar = get_sidebar_announcements_context(
        request, (project, ))
    for k in ["has_sidebar", "is_sidebar_open", "announcements"]:
        assertions[k] = sidebar[0][k]
    view_context_test(ctx, **assertions)


def _test_export_view(project, request, response, kwargs):
    ctx = response.context
    kwargs["project_code"] = project.code
    filter_name, filter_extra = get_filter_name(request.GET)
    form_data = request.GET.copy()
    form_data["path"] = request.path.replace("export-view/", "")
    search_form = UnitExportForm(
        form_data, user=request.user)
    assert search_form.is_valid()
    total, start, end, units_qs = get_search_backend()(
        request.user, **search_form.cleaned_data).search()
    units_qs = units_qs.select_related('store')
    unit_groups = [
        (path, list(units))
        for path, units
        in groupby(
            units_qs,
            lambda x: x.store.pootle_path)]
    assertions = dict(
        project=project,
        language=None,
        source_language="en",
        filter_name=filter_name,
        filter_extra=filter_extra,
        unit_groups=unit_groups)
    view_context_test(ctx, **assertions)


@pytest.mark.django_db
def test_views_project(project_views, settings):
    test_type, project, request, response, kwargs = project_views
    if test_type == "browse":
        _test_browse_view(project, request, response, kwargs)
    elif test_type == "translate":
        _test_translate_view(project, request, response, kwargs, settings)
    if test_type == "export":
        _test_export_view(project, request, response, kwargs)


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
    ob = ProjectSet(user_projects)
    items = [
        make_project_list_item(project)
        for project in ob.children]
    items.sort(lambda x, y: locale.strcoll(x['title'], y['title']))
    table_fields = [
        'name', 'progress', 'total', 'need-translation',
        'suggestions', 'critical', 'last-updated', 'activity']
    table = {
        'id': 'projects',
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': items}

    if request.user.is_superuser:
        url_action_continue = ob.get_translate_url(state='incomplete')
        url_action_fixcritical = ob.get_critical_url()
        url_action_review = ob.get_translate_url(state='suggestions')
        url_action_view_all = ob.get_translate_url(state='all')
    else:
        (url_action_continue,
         url_action_fixcritical,
         url_action_review,
         url_action_view_all) = [None] * 4

    assertions = dict(
        page="browse",
        pootle_path="/projects/",
        resource_path="",
        resource_path_parts=[],
        object=ob,
        table=table,
        browser_extends="projects/all/base.html",
        stats=jsonify(ob.get_stats()),
        check_categories=get_qualitycheck_schema(ob),
        translation_states=get_translation_states(ob),
        url_action_continue=url_action_continue,
        url_action_fixcritical=url_action_fixcritical,
        url_action_review=url_action_review,
        url_action_view_all=url_action_view_all)
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
    assertions = dict(
        page="translate",
        is_admin=False,
        language=None,
        project=None,
        pootle_path="/projects/",
        ctx_path="/projects/",
        resource_path="",
        resource_path_parts=[],
        editor_extends="projects/all/base.html",
        check_categories=get_qualitycheck_schema(),
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


@pytest.mark.django_db
def test_view_projects_export(client):
    response = client.get(reverse("pootle-projects-export"))
    ctx = response.context
    request = response.wsgi_request
    filter_name, filter_extra = get_filter_name(request.GET)
    form_data = request.GET.copy()
    form_data["path"] = request.path.replace("export-view/", "")
    search_form = UnitExportForm(
        form_data, user=request.user)
    assert search_form.is_valid()
    total, start, end, units_qs = get_search_backend()(
        request.user, **search_form.cleaned_data).search()
    units_qs = units_qs.select_related('store')
    unit_groups = [
        (path, list(units))
        for path, units
        in groupby(
            units_qs,
            lambda x: x.store.pootle_path)]
    assertions = dict(
        project=None,
        language=None,
        source_language="en",
        filter_name=filter_name,
        filter_extra=filter_extra,
        unit_groups=unit_groups)
    view_context_test(ctx, **assertions)

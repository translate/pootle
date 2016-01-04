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

from pootle_app.models import Directory
from pootle_app.models.permissions import check_permission
from pootle.core.browser import (
    get_table_headings, make_language_item, make_xlanguage_item,
    make_project_list_item)
from pootle.core.helpers import (
    SIDEBAR_COOKIE_NAME, display_vfolder_priority,
    get_filter_name, get_path_parts, get_sidebar_announcements_context,
    get_step_query)
from pootle.core.utils.json import jsonify
from pootle.core.url_helpers import get_previous_url
from pootle_misc.checks import get_qualitycheck_schema
from pootle_misc.forms import make_search_form
from pootle_misc.stats import get_translation_states
from pootle_project.models import Project, ProjectResource, ProjectSet
from pootle_store.models import Store, Unit

from pootle_pytest.suite import view_context_test


def _test_translate_view(project, request, response, kwargs, settings):
    ctx = response.context
    user = request.profile
    kwargs["project_code"] = project.code
    ctx_path = (
        "/projects/%(project_code)s/" % kwargs)
    resource_path = (
        "%(dir_path)s%(filename)s" % kwargs)
    view_context_test(
        ctx,
        **dict(
            page="translate",
            is_admin=False,
            language=None,
            project=project,
            profile=user,
            pootle_path="%s%s" % (ctx_path, resource_path),
            ctx_path=ctx_path,
            resource_path=resource_path,
            resource_path_parts=get_path_parts(resource_path),
            editor_extends="projects/base.html",
            check_categories=get_qualitycheck_schema(),
            previous_url=get_previous_url(request),
            display_priority=display_vfolder_priority(request),
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
        in ob.get_children_for_user(request.profile)]
    items.sort(lambda x, y: locale.strcoll(x['title'], y['title']))

    table_fields = ['name', 'progress', 'total', 'need-translation',
                    'suggestions', 'critical', 'last-updated', 'activity']
    table = {
        'id': 'project',
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': items}

    assertions = dict(
        page="browse",
        project=project,
        resource_obj=ob,
        browser_extends="projects/base.html",
        pootle_path="/projects/%s" % project_path,
        resource_path=resource_path,
        resource_path_parts=get_path_parts(resource_path),
        url_action_continue=ob.get_translate_url(state='incomplete'),
        url_action_fixcritical=ob.get_critical_url(),
        url_action_review=ob.get_translate_url(state='suggestions'),
        url_action_view_all=ob.get_translate_url(state='all'),
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

    filter_name, filter_extra = get_filter_name(request.GET)
    units_qs = Unit.objects.get_for_path(
        ob.pootle_path, request.profile)
    units_qs = get_step_query(request, units_qs)
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
def test_views_project(site_permissions, project_views, settings):
    test_type, project, request, response, kwargs = project_views
    if test_type == "browse":
        _test_browse_view(project, request, response, kwargs)
    elif test_type == "translate":
        _test_translate_view(project, request, response, kwargs, settings)
    if test_type == "export":
        _test_export_view(project, request, response, kwargs)


@pytest.mark.django_db
def test_view_projects_browse(site_permissions, site_matrix_with_vfolders,
                              site_matrix_with_announcements,
                              client, nobody, default):
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
    assertions = dict(
        page="browse",
        pootle_path="/projects/",
        resource_path="",
        resource_path_parts=[],
        resource_obj=ob,
        table=table,
        browser_extends="projects/all/base.html",
        stats=jsonify(ob.get_stats()),
        check_categories=get_qualitycheck_schema(ob),
        translation_states=get_translation_states(ob),
        url_action_continue=ob.get_translate_url(state='incomplete'),
        url_action_fixcritical=ob.get_critical_url(),
        url_action_review=ob.get_translate_url(state='suggestions'),
        url_action_view_all=ob.get_translate_url(state='all'))
    view_context_test(ctx, **assertions)


@pytest.mark.django_db
def test_view_projects_translate(site_permissions, site_matrix_with_vfolders,
                                 client, nobody, default, settings):
    response = client.get(reverse("pootle-projects-translate"))
    ctx = response.context
    request = response.wsgi_request
    assertions = dict(
        page="translate",
        is_admin=False,
        language=None,
        project=None,
        profile=request.profile,
        pootle_path="/projects/",
        ctx_path="/projects/",
        resource_path="",
        resource_path_parts=[],
        editor_extends="projects/all/base.html",
        check_categories=get_qualitycheck_schema(),
        previous_url=get_previous_url(request),
        display_priority=display_vfolder_priority(request),
        cantranslate=check_permission("translate", request),
        cansuggest=check_permission("suggest", request),
        canreview=check_permission("review", request),
        search_form=make_search_form(request=request),
        current_vfolder_pk="",
        POOTLE_MT_BACKENDS=settings.POOTLE_MT_BACKENDS,
        AMAGAMA_URL=settings.AMAGAMA_URL)
    view_context_test(ctx, **assertions)


@pytest.mark.django_db
def test_view_projects_export(site_permissions, site_matrix_with_vfolders,
                              client, nobody, default):
    response = client.get(reverse("pootle-projects-export"))
    ctx = response.context
    request = response.wsgi_request
    filter_name, filter_extra = get_filter_name(request.GET)
    units_qs = Unit.objects.get_for_path(
        "/projects/", request.profile)
    units_qs = get_step_query(request, units_qs)
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

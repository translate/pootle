# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from itertools import groupby
import json
from urllib import unquote

import pytest

from pytest_pootle.suite import view_context_test

from pootle_app.models import Directory
from pootle_app.models.permissions import check_permission
from pootle.core.browser import (
    get_parent, get_table_headings, make_directory_item, make_store_item)
from pootle.core.helpers import (
    SIDEBAR_COOKIE_NAME,
    get_filter_name, get_sidebar_announcements_context)
from pootle.core.url_helpers import get_previous_url, get_path_parts
from pootle.core.utils.json import jsonify
from pootle_misc.checks import get_qualitycheck_schema
from pootle_misc.forms import make_search_form
from pootle_misc.stats import get_translation_states
from pootle_store.forms import UnitExportForm
from pootle_store.models import Store
from pootle_store.util import get_search_backend
from virtualfolder.helpers import (
    extract_vfolder_from_path, make_vfolder_treeitem_dict)
from virtualfolder.helpers import vftis_for_child_dirs


def _test_browse_view(tp, request, response, kwargs):
    cookie_data = json.loads(
        unquote(response.cookies[SIDEBAR_COOKIE_NAME].value))
    assert cookie_data["foo"] == "bar"
    assert "announcements_projects_%s" % tp.project.code in cookie_data
    assert "announcements_%s" % tp.language.code in cookie_data
    assert (
        "announcements_%s_%s"
        % (tp.language.code, tp.project.code)
        in cookie_data)
    ctx = response.context
    kwargs["project_code"] = tp.project.code
    kwargs["language_code"] = tp.language.code
    resource_path = "%(dir_path)s%(filename)s" % kwargs
    pootle_path = "%s%s" % (tp.pootle_path, resource_path)

    if not (kwargs["dir_path"] or kwargs.get("filename")):
        ob = tp.directory
    elif not kwargs.get("filename"):
        ob = Directory.objects.get(
            pootle_path=pootle_path)
    else:
        ob = Store.objects.get(
            pootle_path=pootle_path)
    if not kwargs.get("filename"):
        vftis = ob.vf_treeitems.select_related("vfolder")
        if not ctx["is_admin"]:
            vftis = vftis.filter(vfolder__is_public=True)
        vfolders = [
            make_vfolder_treeitem_dict(vfolder_treeitem)
            for vfolder_treeitem
            in vftis.order_by('-vfolder__priority')
            if (ctx["is_admin"]
                or vfolder_treeitem.is_visible)]
        stats = {"vfolders": {}}
        for vfolder_treeitem in vfolders or []:
            stats['vfolders'][
                vfolder_treeitem['code']] = vfolder_treeitem["stats"]
            del vfolder_treeitem["stats"]
        if stats["vfolders"]:
            stats.update(ob.get_stats())
        else:
            stats = ob.get_stats()
        stats = jsonify(stats)
    else:
        stats = jsonify(ob.get_stats())
        vfolders = None

    filters = {}
    if vfolders:
        filters['sort'] = 'priority'

    dirs_with_vfolders = vftis_for_child_dirs(ob).values_list(
        "directory__pk", flat=True)
    directories = [
        make_directory_item(
            child,
            **(dict(sort="priority")
               if child.pk in dirs_with_vfolders
               else {}))
        for child in ob.get_children()
        if isinstance(child, Directory)]
    stores = [
        make_store_item(child)
        for child in ob.get_children()
        if isinstance(child, Store)]

    if not kwargs.get("filename"):
        table_fields = [
            'name', 'progress', 'total', 'need-translation',
            'suggestions', 'critical', 'last-updated', 'activity']
        table = {
            'id': 'tp',
            'fields': table_fields,
            'headings': get_table_headings(table_fields),
            'items': directories + stores}
    else:
        table = None

    assertions = dict(
        page="browse",
        object=ob,
        translation_project=tp,
        language=tp.language,
        project=tp.project,
        is_admin=check_permission('administrate', request),
        is_store=(kwargs.get("filename") and True or False),
        browser_extends="translation_projects/base.html",
        pootle_path=pootle_path,
        resource_path=resource_path,
        resource_path_parts=get_path_parts(resource_path),
        translation_states=get_translation_states(ob),
        check_categories=get_qualitycheck_schema(ob),
        url_action_continue=ob.get_translate_url(
            state='incomplete', **filters),
        url_action_fixcritical=ob.get_critical_url(**filters),
        url_action_review=ob.get_translate_url(
            state='suggestions', **filters),
        url_action_view_all=ob.get_translate_url(state='all'),
        stats=stats,
        parent=get_parent(ob))
    if table:
        assertions["table"] = table
    sidebar = get_sidebar_announcements_context(
        request, (tp.project, tp.language, tp))
    for k in ["has_sidebar", "is_sidebar_open", "announcements"]:
        assertions[k] = sidebar[0][k]
    view_context_test(ctx, **assertions)
    if vfolders:
        for vfolder in ctx["vfolders"]["items"]:
            assert (vfolder["is_grayed"] and not ctx["is_admin"]) is False
        assert (
            ctx["vfolders"]["items"]
            == vfolders)

    assert (('display_download' in ctx and ctx['display_download']) ==
            (request.user.is_authenticated()
             and check_permission('translate', request)))


def _test_translate_view(tp, request, response, kwargs, settings):
    ctx = response.context
    kwargs["project_code"] = tp.project.code
    kwargs["language_code"] = tp.language.code
    resource_path = "%(dir_path)s%(filename)s" % kwargs
    request_path = "%s%s" % (tp.pootle_path, resource_path)
    vfolder, pootle_path = extract_vfolder_from_path(request_path)
    current_vfolder_pk = (
        vfolder.pk
        if vfolder
        else "")
    display_priority = (
        not current_vfolder_pk
        and not kwargs['filename'] and ctx['object'].has_vfolders)
    assertions = dict(
        page="translate",
        translation_project=tp,
        language=tp.language,
        project=tp.project,
        is_admin=check_permission('administrate', request),
        ctx_path=tp.pootle_path,
        pootle_path=request_path,
        resource_path=resource_path,
        resource_path_parts=get_path_parts(resource_path),
        editor_extends="translation_projects/base.html",
        check_categories=get_qualitycheck_schema(),
        previous_url=get_previous_url(request),
        current_vfolder_pk=current_vfolder_pk,
        display_priority=display_priority,
        cantranslate=check_permission("translate", request),
        cansuggest=check_permission("suggest", request),
        canreview=check_permission("review", request),
        search_form=make_search_form(request=request),
        POOTLE_MT_BACKENDS=settings.POOTLE_MT_BACKENDS,
        AMAGAMA_URL=settings.AMAGAMA_URL)
    view_context_test(ctx, **assertions)


def _test_export_view(tp, request, response, kwargs):
    ctx = response.context
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
    view_context_test(
        ctx,
        **dict(
            project=tp.project,
            language=tp.language,
            source_language=tp.project.source_language,
            filter_name=filter_name,
            filter_extra=filter_extra,
            unit_groups=unit_groups))


@pytest.mark.django_db
def test_views_tp(tp_views, settings):
    test_type, tp, request, response, kwargs = tp_views
    if test_type == "browse":
        _test_browse_view(tp, request, response, kwargs)
    elif test_type == "translate":
        _test_translate_view(tp, request, response, kwargs, settings)
    else:
        _test_export_view(tp, request, response, kwargs)


@pytest.mark.django_db
def test_view_user_choice(client):

    client.cookies["user-choice"] = "language"
    response = client.get("/foo/bar/baz")
    assert response.status_code == 302
    assert response.get("location") == "http://testserver/foo/"
    assert "user-choice" not in response

    client.cookies["user-choice"] = "project"
    response = client.get("/foo/bar/baz")
    assert response.status_code == 302
    assert response.get("location") == "http://testserver/projects/bar/"
    assert "user-choice" not in response

    client.cookies["user-choice"] = "foo"
    response = client.get("/foo/bar/baz")
    assert response.status_code == 404
    assert "user-choice" not in response


@pytest.mark.django_db
def test_uploads_tp(tp_uploads):
    tp, request, response, kwargs = tp_uploads
    assert response.status_code == 200

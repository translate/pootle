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

from pootle_app.models import Directory
from pootle_app.models.permissions import check_permission
from pootle.core.browser import (
    get_children, get_parent, get_table_headings)
from pootle.core.helpers import (
    SIDEBAR_COOKIE_NAME, display_vfolder_priority,
    get_filter_name, get_sidebar_announcements_context)
from pootle.core.url_helpers import get_previous_url, get_path_parts
from pootle.core.utils.json import jsonify
from pootle_misc.checks import get_qualitycheck_schema
from pootle_misc.forms import make_search_form
from pootle_misc.stats import get_translation_states
from pootle_store.models import Store, Unit
from pootle_store.views import get_step_query
from virtualfolder.helpers import (
    extract_vfolder_from_path, make_vfolder_treeitem_dict)

from pootle_pytest.suite import view_context_test


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

    if resource_path:
        resource_obj = ob
    else:
        resource_obj = tp

    if not kwargs.get("filename"):
        table_fields = [
            'name', 'progress', 'total', 'need-translation',
            'suggestions', 'critical', 'last-updated', 'activity']
        table = {'id': 'tp',
                 'fields': table_fields,
                 'headings': get_table_headings(table_fields),
                 'items': get_children(ob)}
    else:
        table = None

    assertions = dict(
        page="browse",
        translation_project=tp,
        language=tp.language,
        project=tp.project,
        resource_obj=resource_obj,
        is_admin=False,
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
            assert vfolder["is_grayed"] is False
        assert (
            ctx["vfolders"]["items"]
            == vfolders)


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
    assertions = dict(
        page="translate",
        translation_project=tp,
        language=tp.language,
        project=tp.project,
        is_admin=False,
        profile=request.profile,
        ctx_path=tp.pootle_path,
        pootle_path=request_path,
        resource_path=resource_path,
        resource_path_parts=get_path_parts(resource_path),
        editor_extends="translation_projects/base.html",
        check_categories=get_qualitycheck_schema(),
        previous_url=get_previous_url(request),
        current_vfolder_pk=current_vfolder_pk,
        display_priority=display_vfolder_priority(request),
        cantranslate=check_permission("translate", request),
        cansuggest=check_permission("suggest", request),
        canreview=check_permission("review", request),
        search_form=make_search_form(request=request),
        POOTLE_MT_BACKENDS=settings.POOTLE_MT_BACKENDS,
        AMAGAMA_URL=settings.AMAGAMA_URL)
    view_context_test(ctx, **assertions)


def _test_export_view(tp, request, response, kwargs):
    ctx = response.context
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
def test_views_tp(site_permissions, tp_views, settings):
    test_type, tp, request, response, kwargs = tp_views
    if test_type == "browse":
        _test_browse_view(tp, request, response, kwargs)
    elif test_type == "translate":
        _test_translate_view(tp, request, response, kwargs, settings)
    else:
        _test_export_view(tp, request, response, kwargs)

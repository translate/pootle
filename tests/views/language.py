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

from pootle_app.models.permissions import check_permission
from pootle.core.browser import make_project_item, get_table_headings
from pootle.core.helpers import (
    SIDEBAR_COOKIE_NAME,
    get_filter_name, get_sidebar_announcements_context)
from pootle.core.url_helpers import get_previous_url
from pootle.core.utils.json import jsonify
from pootle_misc.checks import get_qualitycheck_schema
from pootle_misc.forms import make_search_form
from pootle_misc.stats import get_translation_states
from pootle_store.forms import UnitExportForm
from pootle_store.util import get_search_backend


def _test_browse_view(language, request, response, kwargs):
    assert (
        response.cookies["pootle-language"].value == language.code)
    cookie_data = json.loads(
        unquote(response.cookies[SIDEBAR_COOKIE_NAME].value))
    assert cookie_data["foo"] == "bar"
    assert "announcements_%s" % language.code in cookie_data
    ctx = response.context
    table_fields = [
        'name', 'progress', 'total', 'need-translation',
        'suggestions', 'critical', 'last-updated', 'activity']
    user_tps = language.get_children_for_user(request.user)
    items = [make_project_item(tp) for tp in user_tps]
    table = {
        'id': 'language',
        'fields': table_fields,
        'headings': get_table_headings(table_fields),
        'items': items}
    assertions = dict(
        page="browse",
        object=language,
        language={
            'code': language.code,
            'name': language.name},
        browser_extends="languages/base.html",
        pootle_path="/%s/" % language.code,
        resource_path="",
        resource_path_parts=[],
        url_action_continue=language.get_translate_url(state='incomplete'),
        url_action_fixcritical=language.get_critical_url(),
        url_action_review=language.get_translate_url(state='suggestions'),
        url_action_view_all=language.get_translate_url(state='all'),
        # check_categories=get_qualitycheck_schema(language),
        table=table,
        translation_states=get_translation_states(language),
        stats=jsonify(language.get_stats_for_user(request.user)))
    sidebar = get_sidebar_announcements_context(
        request, (language, ))
    for k in ["has_sidebar", "is_sidebar_open", "announcements"]:
        assertions[k] = sidebar[0][k]
    view_context_test(ctx, **assertions)


def _test_translate_view(language, request, response, kwargs, settings):
    ctx = response.context
    view_context_test(
        ctx,
        **dict(
            project=None,
            language=language,
            page="translate",
            ctx_path=language.directory.pootle_path,
            pootle_path=language.directory.pootle_path,
            resource_path="",
            resource_path_parts=[],
            editor_extends="languages/base.html",
            check_categories=get_qualitycheck_schema(),
            previous_url=get_previous_url(request),
            display_priority=False,
            is_admin=check_permission('administrate', request),
            cantranslate=check_permission("translate", request),
            cansuggest=check_permission("suggest", request),
            canreview=check_permission("review", request),
            search_form=make_search_form(request=request),
            current_vfolder_pk="",
            POOTLE_MT_BACKENDS=settings.POOTLE_MT_BACKENDS,
            AMAGAMA_URL=settings.AMAGAMA_URL))


def _test_export_view(language, request, response, kwargs):
    # TODO: export views should be parsed in a form
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
            project=None,
            language=language,
            source_language="en",
            filter_name=filter_name,
            filter_extra=filter_extra,
            unit_groups=unit_groups))


@pytest.mark.django_db
def test_views_language(language_views, settings):
    test_type, language, request, response, kwargs = language_views
    if test_type == "browse":
        _test_browse_view(language, request, response, kwargs)
    if test_type == "translate":
        _test_translate_view(language, request, response, kwargs, settings)
    elif test_type == "export":
        _test_export_view(language, request, response, kwargs)

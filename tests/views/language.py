# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict

import pytest

from pytest_pootle.suite import view_context_test

from pootle_app.models.permissions import check_permission
from pootle.core.browser import make_project_item
from pootle.core.delegate import scores
from pootle.core.helpers import get_sidebar_announcements_context
from pootle.core.url_helpers import get_previous_url
from pootle.core.utils.stats import (
    TOP_CONTRIBUTORS_CHUNK_SIZE, get_translation_states)
from pootle.core.views.browse import StatsDisplay
from pootle.core.views.display import ChecksDisplay
from pootle_checks.constants import CATEGORY_IDS, CHECK_NAMES
from pootle_checks.utils import get_qualitychecks, get_qualitycheck_schema
from pootle_misc.forms import make_search_form


def _test_browse_view(language, request, response, kwargs):
    assert response.cookies["pootle-language"].value == language.code
    assert (request.user.is_anonymous
            or "announcements/%s" % language.code in request.session)
    ctx = response.context
    user_tps = language.get_children_for_user(request.user)
    stats = language.data_tool.get_stats(user=request.user)
    items = [make_project_item(tp) for tp in user_tps]
    for item in items:
        if item["code"] in stats["children"]:
            item["stats"] = stats["children"][item["code"]]
    checks = ChecksDisplay(language).checks_by_category
    stats = StatsDisplay(language, stats=stats).stats
    del stats["children"]
    score_data = scores.get(language.__class__)(language)
    chunk_size = TOP_CONTRIBUTORS_CHUNK_SIZE

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
        translation_states=get_translation_states(language),
        top_scorers=top_scorer_data,
        checks=checks,
        stats=stats)
    sidebar = get_sidebar_announcements_context(request, (language, ))
    for k in ["has_sidebar", "is_sidebar_open", "announcements"]:
        assertions[k] = sidebar[k]
    view_context_test(ctx, **assertions)


def _test_translate_view(language, request, response, kwargs, settings):
    ctx = response.context
    checks = get_qualitychecks()
    schema = {sc["code"]: sc for sc in get_qualitycheck_schema()}
    check_data = language.data_tool.get_checks()
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
            project=None,
            language=language,
            page="translate",
            ctx_path=language.directory.pootle_path,
            pootle_path=language.directory.pootle_path,
            resource_path="",
            resource_path_parts=[],
            editor_extends="languages/base.html",
            checks=_checks,
            previous_url=get_previous_url(request),
            display_priority=False,
            has_admin_access=check_permission('administrate', request),
            cantranslate=check_permission("translate", request),
            cansuggest=check_permission("suggest", request),
            canreview=check_permission("review", request),
            search_form=make_search_form(request=request),
            current_vfolder_pk="",
            POOTLE_MT_BACKENDS=settings.POOTLE_MT_BACKENDS,
            AMAGAMA_URL=settings.AMAGAMA_URL))


@pytest.mark.django_db
def test_views_language(language_views, settings):
    test_type, language, request, response, kwargs = language_views
    if test_type == "browse":
        _test_browse_view(language, request, response, kwargs)
    if test_type == "translate":
        _test_translate_view(language, request, response, kwargs, settings)

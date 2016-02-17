#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
from datetime import datetime, timedelta
import functools
import json
import urllib

import pytest

from django.core.urlresolvers import reverse

from pytest_pootle.env import TEST_USERS
from pytest_pootle.utils import create_store, get_translated_uids


DAY_AGO = (datetime.now() - timedelta(days=1))
MONTH_AGO = (datetime.now() - timedelta(days=30))
TWO_MONTHS_AGO = (datetime.now() - timedelta(days=60))

BAD_VIEW_TESTS = OrderedDict(
    (("/foo/bar", dict(code=301, location="/foo/bar/")),
     ("/foo/bar/", {}),
     ("/projects", dict(code=301, location="/projects/")),
     ("/projects/project0",
      dict(code=301, location="/projects/project0/")),
     ("/projects/project0/foo.po", {}),
     ("/projects/projectfoo",
      dict(code=301, location="/projects/projectfoo/")),
     ("/projects/projectfoo/", {}),
     ("/language0/projectfoo",
      dict(code=301, location="/language0/projectfoo/")),
     ("/language0/projectfoo/", {}),
     ("/language0/project0",
      dict(code=301, location="/language0/project0/")),
     ("/projects/project0/subdir0/foo.po", {}),
     # these may not be correct - but are current behaviour
     ("/language0/project0/foo/",
      dict(code=302, location="/language0/project0/")),
     ("/language0/project0/foo",
      dict(code=302, location="/language0/project0/")),
     ("/language0/project0/subdir0",
      dict(code=302, location="/language0/project0/")),

     ("/projects/PROJECT0/", {}),
     ("/language0/PROJECT0/", {}),
     ("/language0/PROJECT0/subdir0/", {}),
     ("/language0/PROJECT0/store0.po", {}),

     ("/LANGUAGE0/",
      dict(code=301, location="/language0/")),
     ("/LANGUAGE0/foo/",
      dict(code=301, location="/language0/foo/")),
     ("/LANGUAGE0/project0/",
      dict(code=301, location="/language0/project0/")),
     ("/LANGUAGE0/project0/subdir0/",
      dict(code=301, location="/language0/project0/subdir0/")),
     ("/LANGUAGE0/project0/store0.po",
      dict(code=301, location="/language0/project0/store0.po")),

     ("/xhr/units/?path=/%s" % ("BAD" * 800),
      dict(ajax=True, code=400)),
     ("/xhr/units?filter=translated&path=/&initial=True&uids=75000",
      dict(ajax=True))))

GET_UNITS_TESTS = OrderedDict(
    (("default_path", {}),
     ("state_translated",
      {"filter": "translated"}),
     ("state_translated_continued",
      {"filter": "translated",
       "uids": functools.partial(get_translated_uids, count=9),
       "initial": False}),
     ("state_untranslated",
      {"filter": "untranslated"}),
     ("state_incomplete",
      {"filter": "incomplete"}),
     ("state_fuzzy",
      {"filter": "fuzzy"}),
     ("sort_units_oldest",
      {"sort_by_param": "oldest"}),
     ("filter_translated_from_uid",
      {"uids": get_translated_uids,
       "filter": "translated"}),
     ("filter_translated_from_uid_sort_priority",
      {"uids": get_translated_uids,
       "filter": "translated",
       "sort": "priority"}),
     ("translated_by_member",
      {"filter": "translated",
       "user": "member"}),
     ("translated_by_member_FOO",
      {"filter": "translated",
       "user": "member_FOO"}),
     ("modified_last_month",
      {"filter": "translated",
       "modified-since": MONTH_AGO.isoformat()}),
     ("modified_last_calendar_month",
      {"filter": "translated",
       "month": MONTH_AGO.strftime("%Y-%m")}),
     ("modified_last_two_months",
      {"modified_since": TWO_MONTHS_AGO.isoformat()}),
     ("modified_last_day",
      {"modified_since": DAY_AGO.isoformat()}),
     ("path_vfolder",
      {"path": "/language0/project0/virtualfolder0/"}),
     ("filter_suggestions",
      {"filter": "suggestions"}),
     ("filter_user_suggestions",
      {"filter": "user-suggestions"}),
     ("filter_user_suggestions_accepted",
      {"filter": "user-suggestions-accepted"}),
     ("filter_user_suggestions_rejected",
      {"filter": "user-suggestions-rejected"}),
     ("filter_user_submissions",
      {"filter": "user-submissions"}),
     ("filter_user_submissions_overwritten",
      {"filter": "user-submissions-overwritten"}),
     ("filter_search_empty",
      {"search": "FOO",
       "sfields": "source"}),
     ("filter_search_untranslated",
      {"search": "untranslated",
       "sfields": "source"}),
     ("filter_search_sfields_multi",
      {"search": "FOO",
       "sfields": "source,target"}),
     ("sort_user_suggestion_newest",
      {"sort": "newest",
       "filter": "user-suggestions"}),
     ("sort_user_suggestion_oldest",
      {"sort": "oldest",
       "filter": "user-suggestions"}),
     ("checks_foo",
      {"filter": "checks",
       "checks": "foo"}),
     ("checks_endpunc",
      {"filter": "checks",
       "checks": ["endpunc"]}),
     ("checks_category_critical",
      {"filter": "checks",
       "category": "critical"}),
     ("checks_category_critical",
      {"filter": "checks",
       "category": "critical"})))

LANGUAGE_VIEW_TESTS = OrderedDict(
    (("browse", {}),
     ("translate", {}),
     ("export", {})))

PROJECT_VIEW_TESTS = OrderedDict(
    (("browse", {}),
     ("browse_directory",
      {"dir_path": "subdir0/"}),
     ("browse_store",
      {"filename": "store0.po"}),
     ("browse_directory_store",
      {"dir_path": "subdir0/",
       "filename": "store3.po"}),
     ("translate", {}),
     ("translate_directory",
      {"dir_path": "subdir0/"}),
     ("translate_store",
      {"filename": "store0.po"}),
     ("translate_directory_store",
      {"dir_path": "subdir0/",
       "filename": "store3.po"}),
     ("export", {}),
     ("export_directory",
      {"dir_path": "subdir0/"}),
     ("export_store",
      {"filename": "store0.po"}),
     ("export_directory_store",
      {"dir_path": "subdir0/",
       "filename": "store3.po"})))

TP_VIEW_TESTS = OrderedDict(
    (("browse", {}),
     ("browse_directory",
      {"dir_path": "subdir0/"}),
     ("browse_store",
      {"filename": "store0.po"}),
     ("browse_directory_store",
      {"dir_path": "subdir0/",
       "filename": "store3.po"}),
     ("translate", {}),
     ("translate_directory",
      {"dir_path": "subdir0/"}),
     ("translate_store",
      {"filename": "store0.po"}),
     ("translate_directory_store",
      {"dir_path": "subdir0/",
       "filename": "store3.po"}),
     ("translate_vfolder",
      {"dir_path": "virtualfolder0/"}),
     ("export", {}),
     ("export_directory",
      {"dir_path": "subdir0/"}),
     ("export_store",
      {"filename": "store0.po"}),
     ("export_directory_store",
      {"dir_path": "subdir0/",
       "filename": "store3.po"})))


@pytest.fixture(params=GET_UNITS_TESTS.keys())
def get_units_views(request, client, request_users):
    params = GET_UNITS_TESTS[request.param].copy()
    params["path"] = params.get("path", "/")

    if "initial" in params and not params["initial"]:
        del params["initial"]
    else:
        params["initial"] = "true"

    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    if "uids" in params and callable(params["uids"]):
        params["uids"] = ",".join(str(uid) for uid in params["uids"]())

    url_params = urllib.urlencode(params, True)
    response = client.get(
        "%s?%s"
        % (reverse("pootle-xhr-units"),
           url_params),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    params["pootle_path"] = params["path"]
    return user, params, url_params, response


@pytest.fixture(params=PROJECT_VIEW_TESTS.keys())
def project_views(request, client):
    from pootle.core.helpers import SIDEBAR_COOKIE_NAME
    from pootle_project.models import Project

    test_type = request.param.split("_")[0]
    project = Project.objects.all()[0]
    kwargs = {"project_code": project.code, "dir_path": "", "filename": ""}
    kwargs.update(PROJECT_VIEW_TESTS[request.param])
    view_name = "pootle-project-%s" % test_type
    client.cookies[SIDEBAR_COOKIE_NAME] = json.dumps({"foo": "bar"})
    response = client.get(reverse(view_name, kwargs=kwargs))
    return test_type, project, response.wsgi_request, response, kwargs


@pytest.fixture(params=TP_VIEW_TESTS.keys())
def tp_view_test_names(request):
    return request.param


@pytest.fixture(params=(None, 'member', 'admin'))
def tp_view_usernames(request):
    return request.param


@pytest.fixture
def tp_views(tp_view_test_names, tp_view_usernames, client):
    from pootle.core.helpers import SIDEBAR_COOKIE_NAME
    from pootle_translationproject.models import TranslationProject

    test_type = tp_view_test_names.split("_")[0]
    tp = TranslationProject.objects.all()[0]
    tp_view = "pootle-tp"
    kwargs = {
        "project_code": tp.project.code,
        "language_code": tp.language.code,
        "dir_path": "",
        "filename": ""}
    kwargs.update(TP_VIEW_TESTS[tp_view_test_names])
    client.cookies[SIDEBAR_COOKIE_NAME] = json.dumps({"foo": "bar"})
    if kwargs.get("filename"):
        tp_view = "%s-store" % tp_view
    else:
        del kwargs["filename"]
    view_name = "%s-%s" % (tp_view, test_type)
    if tp_view_usernames is not None:
        password = TEST_USERS[tp_view_usernames]['password']
        client.login(username=tp_view_usernames, password=password)
    response = client.get(reverse(view_name, kwargs=kwargs))
    kwargs["filename"] = kwargs.get("filename", "")
    return test_type, tp, response.wsgi_request, response, kwargs


@pytest.fixture(params=LANGUAGE_VIEW_TESTS.keys())
def language_views(request, client):

    from pootle.core.helpers import SIDEBAR_COOKIE_NAME
    from pootle_language.models import Language

    test_type = request.param.split("_")[0]
    language = Language.objects.get(code="language0")
    kwargs = {"language_code": language.code}
    kwargs.update(LANGUAGE_VIEW_TESTS[request.param])
    view_name = "pootle-language-%s" % test_type
    client.cookies[SIDEBAR_COOKIE_NAME] = json.dumps({"foo": "bar"})
    response = client.get(reverse(view_name, kwargs=kwargs))
    return test_type, language, response.wsgi_request, response, kwargs


@pytest.fixture(params=BAD_VIEW_TESTS.keys())
def bad_views(request, client):
    test = dict(code=404)
    test.update(BAD_VIEW_TESTS[request.param])
    if test.get("ajax"):
        response = client.get(request.param, HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    else:
        response = client.get(request.param)
    return (
        request.param,
        response,
        test)


@pytest.fixture
def tp_uploads(client, member):
    from pootle_translationproject.models import TranslationProject
    from pootle_store.models import Store

    tp = TranslationProject.objects.all()[0]
    store = Store.objects.filter(parent=tp.directory)[0]
    kwargs = {
        "project_code": tp.project.code,
        "language_code": tp.language.code,
        "dir_path": "",
        "filename": store.name}
    password = TEST_USERS[member.username]['password']
    client.login(username=member.username, password=password)
    response = client.post(
        reverse("pootle-tp-store-browse", kwargs=kwargs),
        {'name': '', 'attachment': create_store([
            (unit.source_f, "%s UPDATED" % unit.target_f)
            for unit in store.units])})

    return tp, response.wsgi_request, response, kwargs

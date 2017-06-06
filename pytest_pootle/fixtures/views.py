# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools
import urllib
from collections import OrderedDict
from datetime import timedelta

import pytest
from dateutil.relativedelta import relativedelta
from pytest_pootle.fixtures.models.user import TEST_USERS
from pytest_pootle.utils import create_store, get_test_uids

from django.core.files.uploadedfile import SimpleUploadedFile
from django.urls import reverse
from django.utils import timezone


DAY_AGO = (timezone.now() - timedelta(days=1))
MONTH_AGO = (timezone.now() - relativedelta(months=1))
TWO_MONTHS_AGO = (timezone.now() - relativedelta(months=2))
SEVEN_MONTHS_AGO = (timezone.now() - relativedelta(months=7))

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

     ("/xhr/units/1/edit/", dict(code=400)),
     ("/xhr/units/?path=/%s" % ("BAD" * 800),
      dict(ajax=True, code=400)),
     ("/xhr/units?filter=translated&"
      "path=/",
      dict(ajax=True))))

GET_UNITS_TESTS = OrderedDict(
    (("default_path", {}),
     ("root_path", dict(path="/")),
     ("projects_path", dict(path="/projects/")),
     ("project_path", dict(path="/projects/project0/")),
     ("bad_project_path", dict(path="/projects/FOO/")),
     ("state_translated",
      {"filter": "translated"}),
     ("state_translated_continued",
      {"filter": "translated",
       "uids": functools.partial(get_test_uids, count=9),
       "offset": 10}),
     ("state_untranslated",
      {"filter": "untranslated"}),
     ("state_untranslated",
      {"filter": "untranslated",
       "offset": 100000}),
     ("state_incomplete",
      {"filter": "incomplete"}),
     ("state_fuzzy",
      {"filter": "fuzzy"}),
     ("sort_units_oldest",
      {"sort_by_param": "oldest"}),
     ("filter_from_uid",
      {"path": "/language0/project0/store0.po",
       "uids": functools.partial(get_test_uids,
                                 pootle_path="/language0/project0/store0.po"),
       "filter": "all"}),
     ("filter_from_uid_sort_priority",
      {"uids": functools.partial(get_test_uids,
                                 pootle_path="/language0/project0/store0.po"),
       "filter": "all",
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
     ("modified_calendar_month_7_month_ago",
      {"filter": "translated",
       "month": SEVEN_MONTHS_AGO.strftime("%Y-%m")}),
     ("modified_last_two_months",
      {"modified_since": TWO_MONTHS_AGO.isoformat()}),
     ("modified_last_day",
      {"modified_since": DAY_AGO.isoformat()}),
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
      {"search": "SEARCH_NOT_EXIST",
       "sfields": "source"}),
     ("filter_search_untranslated",
      {"search": "untranslated",
       "sfields": "source"}),
     ("filter_search_sfields_multi",
      {"search": "SEARCH_NOT_EXIST",
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
       "category": "critical"})))

GET_VFOLDER_UNITS_TESTS = OrderedDict(
    (("path_vfolder",
      {"path": "/++vfolder/virtualfolder0/language0/project0/translate/"}), ))

LANGUAGE_VIEW_TESTS = OrderedDict(
    (("browse", {}),
     ("translate", {})))

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
     ("translate_no_vfolders_in_subdir",
      {"dir_path": "subdir0/subdir1/"})))

VFOLDER_VIEW_TESTS = OrderedDict(
    (("translate_vfolder",
      {"dir_path": ""}),
     ("translate_vfolder_subdir",
      {"dir_path": "subdir0/"})))

DISABLED_PROJECT_URL_PARAMS = OrderedDict(
    (("project", {
        "view_name": "pootle-project",
        "project_code": "disabled_project0",
        "dir_path": "",
        "filename": ""}),
     ("tp", {
         "view_name": "pootle-tp",
         "project_code": "disabled_project0",
         "language_code": "language0",
         "dir_path": ""}),
     ("tp_subdir", {
         "view_name": "pootle-tp",
         "project_code": "disabled_project0",
         "language_code": "language0",
         "dir_path": "subdir0/"}),
     ("tp_store", {
         "view_name": "pootle-tp-store",
         "project_code": "disabled_project0",
         "language_code": "language0",
         "dir_path": "",
         "filename": "store0.po"}),
     ("tp_subdir_store", {
         "view_name": "pootle-tp-store",
         "project_code": "disabled_project0",
         "language_code": "language0",
         "dir_path": "subdir0/",
         "filename": "store1.po"})))


@pytest.fixture(params=GET_UNITS_TESTS.keys())
def get_units_views(request, client, request_users):
    params = GET_UNITS_TESTS[request.param].copy()
    params["path"] = params.get("path", "/language0/")

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
def project_views(request, client, request_users, settings):
    from pootle_project.models import Project

    test_kwargs = PROJECT_VIEW_TESTS[request.param].copy()
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])

    test_type = request.param.split("_")[0]
    project = Project.objects.get(code="project0")
    kwargs = {"project_code": project.code, "dir_path": "", "filename": ""}
    kwargs.update(test_kwargs)
    view_name = "pootle-project-%s" % test_type
    response = client.get(reverse(view_name, kwargs=kwargs))
    return test_type, project, response.wsgi_request, response, kwargs


@pytest.fixture(params=TP_VIEW_TESTS.keys())
def tp_views(request, client, request_users, settings):
    from pootle_translationproject.models import TranslationProject

    tp_view_test_names = request.param
    user = request_users["user"]

    test_type = tp_view_test_names.split("_")[0]
    tp = TranslationProject.objects.all()[0]
    tp_view = "pootle-tp"
    kwargs = {
        "project_code": tp.project.code,
        "language_code": tp.language.code,
        "dir_path": "",
        "filename": ""}
    test_kwargs = TP_VIEW_TESTS[request.param].copy()
    kwargs.update(test_kwargs)
    if kwargs.get("filename"):
        tp_view = "%s-store" % tp_view
    else:
        del kwargs["filename"]
    view_name = "%s-%s" % (tp_view, test_type)

    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    response = client.get(reverse(view_name, kwargs=kwargs))
    kwargs["filename"] = kwargs.get("filename", "")
    return test_type, tp, response.wsgi_request, response, kwargs


@pytest.fixture(params=LANGUAGE_VIEW_TESTS.keys())
def language_views(request, client):

    from pootle_language.models import Language

    test_type = request.param.split("_")[0]
    language = Language.objects.get(code="language0")
    kwargs = {"language_code": language.code}
    kwargs.update(LANGUAGE_VIEW_TESTS[request.param])
    view_name = "pootle-language-%s" % test_type
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


@pytest.fixture(params=[
    ("member", "member", {}),
    # member doesn't have administarate permissions to set member2 as uploader
    ("member", "member2", {"user_id": ""}),
    ("admin", "member2", {}),
])
def tp_uploads(request, client):
    from pootle.core.delegate import language_team
    from pootle_language.models import Language
    from pootle_translationproject.models import TranslationProject
    from pootle_store.models import Store
    from django.contrib.auth import get_user_model

    submitter_name, uploader_name, errors = request.param
    uploader = get_user_model().objects.get(username=uploader_name)
    tp = TranslationProject.objects.all()[0]
    store = Store.objects.filter(parent=tp.directory)[0]
    kwargs = {
        "project_code": tp.project.code,
        "language_code": tp.language.code,
        "dir_path": "",
        "filename": store.name}
    password = TEST_USERS[submitter_name]['password']
    language_team.get(Language)(tp.language).add_member(uploader, "submitter")
    client.login(username=submitter_name, password=password)
    updated_units = [
        (unit.source_f, "%s UPDATED" % unit.target_f, False)
        for unit in store.units
    ]
    updated_store = create_store(store.pootle_path, "0", updated_units)
    uploaded_file = SimpleUploadedFile(
        store.name,
        str(updated_store),
        "text/x-gettext-translation"
    )
    response = client.post(
        reverse("pootle-tp-store-browse", kwargs=kwargs),
        {
            'name': '',
            'file': uploaded_file,
            'user_id': uploader.id
        }
    )

    return tp, response.wsgi_request, response, kwargs, errors


@pytest.fixture(params=("browse", "translate"))
def view_types(request):
    """List of possible view types."""
    return request.param


@pytest.fixture(params=DISABLED_PROJECT_URL_PARAMS.keys())
def dp_view_urls(request, view_types):
    """List of url params required for disabled project tests."""
    kwargs = DISABLED_PROJECT_URL_PARAMS[request.param].copy()
    view_name = kwargs.pop("view_name")
    view_name = "%s-%s" % (view_name, view_types)

    return reverse(view_name, kwargs=kwargs)


@pytest.fixture(params=VFOLDER_VIEW_TESTS.keys())
def vfolder_views(request, client, request_users, settings, tp0):

    vfolder0 = tp0.stores.filter(
        vfolders__isnull=False)[0].vfolders.first()
    test_kwargs = VFOLDER_VIEW_TESTS[request.param].copy()
    tp_view_test_names = request.param
    user = request_users["user"]
    test_type = tp_view_test_names.split("_")[0]
    tp_view = "pootle-vfolder-tp"
    kwargs = {
        "vfolder_name": vfolder0.name,
        "project_code": tp0.project.code,
        "language_code": tp0.language.code,
        "dir_path": "",
        "filename": ""}
    kwargs.update(test_kwargs)
    del kwargs["filename"]
    view_name = "%s-%s" % (tp_view, test_type)
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    response = client.get(reverse(view_name, kwargs=kwargs))
    kwargs["filename"] = kwargs.get("filename", "")
    return test_type, tp0, response.wsgi_request, response, kwargs


@pytest.fixture(params=GET_VFOLDER_UNITS_TESTS.keys())
def get_vfolder_units_views(request, client, request_users):
    from virtualfolder.models import VirtualFolder

    params = GET_VFOLDER_UNITS_TESTS[request.param].copy()
    params["path"] = params.get("path", "/language0/")
    vfolder0 = VirtualFolder.objects.first()
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    url_params = urllib.urlencode(params, True)
    response = client.get(
        "%s?%s"
        % (reverse("vfolder-pootle-xhr-units",
                   kwargs=dict(vfolder_name=vfolder0.name)),
           url_params),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    params["pootle_path"] = params["path"]
    return user, vfolder0, params, url_params, response

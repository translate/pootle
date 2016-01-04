#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from collections import OrderedDict
import json

import pytest

from django.core.urlresolvers import reverse


BAD_VIEW_TESTS = OrderedDict(
    (("/foo/bar", dict(code=301, location="/foo/bar/")),
     ("/foo/bar/", {}),
     ("/projects", dict(code=301, location="/projects/")),
     ("/projects/project0",
      dict(code=301, location="/projects/project0/")),
     ("/projects/projectfoo",
      dict(code=301, location="/projects/projectfoo/")),
     ("/projects/projectfoo/", {}),
     ("/language0/projectfoo",
      dict(code=301, location="/language0/projectfoo/")),
     ("/language0/projectfoo/", {}),
     ("/language0/project0",
      dict(code=301, location="/language0/project0/"))))

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


@pytest.fixture
def admin_client(admin, client):
    """A Django test client logged in as an admin user."""
    client.login(username=admin.username, password='admin')
    return client


@pytest.fixture
def project_views(site_permissions, project_view_names,
                  site_matrix_with_vfolders, site_matrix_with_subdirs,
                  site_matrix_with_announcements,
                  default, client, nobody):
    from pootle.core.helpers import SIDEBAR_COOKIE_NAME
    from pootle_project.models import Project

    test_type = project_view_names.split("_")[0]
    project = Project.objects.all()[0]
    kwargs = {"project_code": project.code, "dir_path": "", "filename": ""}
    kwargs.update(PROJECT_VIEW_TESTS[project_view_names])
    view_name = "pootle-project-%s" % test_type
    client.cookies[SIDEBAR_COOKIE_NAME] = json.dumps({"foo": "bar"})
    response = client.get(reverse(view_name, kwargs=kwargs))
    return test_type, project, response.wsgi_request, response, kwargs


@pytest.fixture
def tp_views(site_permissions, tp_view_names, site_matrix_with_vfolders,
             site_matrix_with_subdirs, site_matrix_with_announcements,
             default, nobody, client):
    from pootle.core.helpers import SIDEBAR_COOKIE_NAME
    from pootle_translationproject.models import TranslationProject

    test_type = tp_view_names.split("_")[0]
    tp = TranslationProject.objects.all()[0]
    kwargs = {
        "project_code": tp.project.code,
        "language_code": tp.language.code,
        "dir_path": "",
        "filename": ""}
    kwargs.update(TP_VIEW_TESTS[tp_view_names])
    view_name = "pootle-tp-%s" % test_type
    client.cookies[SIDEBAR_COOKIE_NAME] = json.dumps({"foo": "bar"})
    response = client.get(reverse(view_name, kwargs=kwargs))
    return test_type, tp, response.wsgi_request, response, kwargs


@pytest.fixture
def language_views(site_permissions, language_view_names,
                   site_matrix_with_vfolders, site_matrix_with_subdirs,
                   site_matrix_with_announcements,
                   default, nobody, client):

    from pootle.core.helpers import SIDEBAR_COOKIE_NAME
    from pootle_language.models import Language

    test_type = language_view_names.split("_")[0]
    language = Language.objects.all()[0]
    kwargs = {"language_code": language.code}
    kwargs.update(LANGUAGE_VIEW_TESTS[language_view_names])
    view_name = "pootle-language-%s" % test_type
    client.cookies[SIDEBAR_COOKIE_NAME] = json.dumps({"foo": "bar"})
    response = client.get(reverse(view_name, kwargs=kwargs))
    return test_type, language, response.wsgi_request, response, kwargs


@pytest.fixture
def bad_views(site_permissions, bad_view_names,
              site_matrix_with_vfolders, site_matrix_with_subdirs,
              site_matrix_with_announcements,
              default, nobody, client):
    test = dict(code=404)
    test.update(BAD_VIEW_TESTS[bad_view_names])
    return (
        bad_view_names,
        client.get(bad_view_names),
        test)

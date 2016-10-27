# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import sys
from collections import OrderedDict

import pytest

from pytest_pootle.fixtures.models.user import TEST_USERS

from django.urls import reverse

from pootle_fs.forms import LangMappingFormSet, ProjectFSAdminForm

from .forms import _get_management_data


@pytest.mark.django_db
def test_view_fs_project_admin_form(client, project0, request_users):
    user = request_users["user"]
    admin_url = reverse(
        'pootle-admin-project-fs',
        kwargs=dict(project_code=project0.code))
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(admin_url)
    if not user.is_superuser:
        assert response.status_code == 403
        return
    assert isinstance(response.context["form"], ProjectFSAdminForm)
    assert response.context["form"].project == project0
    assert isinstance(
        response.context["lang_mapping_formset"],
        LangMappingFormSet)


@pytest.mark.django_db
def test_view_fs_project_admin_post(client, project0, request_users):
    user = request_users["user"]
    admin_url = reverse(
        'pootle-admin-project-fs',
        kwargs=dict(project_code=project0.code))
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.post(
        admin_url,
        dict(foo="bar"))
    if not user.is_superuser:
        if user.is_anonymous:
            assert response.status_code == 402
        else:
            assert response.status_code == 403
        return
    # as there are multiple forms, if you post and the default form
    # is not posted, you get the GET
    assert response.status_code == 200


@pytest.mark.django_db
@pytest.mark.xfail(sys.platform == 'win32',
                   reason="path mangling broken on windows")
def test_view_fs_project_admin_post_config(client, project0, request_users):
    user = request_users["user"]
    admin_url = reverse(
        'pootle-admin-project-fs',
        kwargs=dict(project_code=project0.code))
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.post(
        admin_url,
        {'fs-config-fs_type': "localfs",
         'fs-config-fs_url': "/foo/bar",
         'fs-config-translation_mapping': (
             "/trans/<language_code>/<filename>.<ext>")})
    if not user.is_superuser:
        if user.is_anonymous:
            assert response.status_code == 402
        else:
            assert response.status_code == 403
        return
    assert response.status_code == 302
    assert response.get("location") == admin_url
    assert project0.config["pootle_fs.fs_type"] == "localfs"
    assert project0.config["pootle_fs.fs_url"] == "/foo/bar"
    assert project0.config["pootle_fs.translation_mappings"] == dict(
        default="/trans/<language_code>/<filename>.<ext>")


@pytest.mark.django_db
def test_view_fs_project_admin_post_lang_mapper(client, admin, project0, language0):
    password = TEST_USERS[admin.username]["password"]
    client.login(username=admin.username, password=password)
    admin_url = reverse(
        'pootle-admin-project-fs',
        kwargs=dict(project_code=project0.code))
    got = client.get(admin_url)
    formset = got.context["lang_mapping_formset"]
    data = _get_management_data(formset)
    data["lang-mapping-0-pootle_code"] = language0.code
    data["lang-mapping-0-fs_code"] = "FOO"
    response = client.post(admin_url, data)
    assert len(response.context["lang_mapping_formset"].forms) == 2
    assert (
        project0.config["pootle.core.lang_mapping"]
        == OrderedDict([(u'FOO', u'language0')]))

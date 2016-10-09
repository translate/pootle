# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.urlresolvers import reverse

from pootle_fs.forms import ProjectFSAdminForm


@pytest.mark.django_db
def test_form_fs_project_admin_view(client, project0, request_users):
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


@pytest.mark.django_db
def test_form_fs_project_admin_post(client, project0, request_users):
    user = request_users["user"]
    admin_url = reverse(
        'pootle-admin-project-fs',
        kwargs=dict(project_code=project0.code))
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.post(
        admin_url,
        dict(
            fs_type="localfs",
            fs_url="/foo/bar",
            translation_path="/trans/<language_code>/<filename>.<ext>"))
    if not user.is_superuser:
        if user.is_anonymous():
            assert response.status_code == 402
        else:
            assert response.status_code == 403
        return
    assert response.status_code == 302
    assert response.get("location") == admin_url
    assert project0.config["pootle_fs.fs_type"] == "localfs"
    assert project0.config["pootle_fs.fs_url"] == "/foo/bar"
    assert project0.config["pootle_fs.translation_paths"] == dict(
        default="/trans/<language_code>/<filename>.<ext>")

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.urls import reverse


@pytest.mark.django_db
def test_views_disabled_project(client, dp_view_urls, request_users):
    url = dp_view_urls
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    response = client.get(url)

    if user.is_superuser:
        assert response.status_code == 200
    else:
        assert response.status_code == 404


@pytest.mark.django_db
def test_disabled_project_in_lang_browse_view(client, request_users):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    response = client.get(reverse("pootle-language-browse",
                                  kwargs={"language_code": "language0"}))

    disabled_project_exists = "language0-disabled_project0" in response.content

    assert response.status_code == 200
    assert (user.is_superuser is disabled_project_exists)

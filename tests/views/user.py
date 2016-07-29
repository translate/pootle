# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.mark.django_db
def test_user_stats_link(client, request_users):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    response = client.get("/user/member/")
    assert (
        ("user-detailed-stats" in response.content)
        == (not user.is_anonymous()))


@pytest.mark.django_db
def test_user_stats_view(client, request_users):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    response = client.get("/user/member/stats/")
    assert (
        (response.status_code)
        == (user.is_anonymous() and 302 or 200))

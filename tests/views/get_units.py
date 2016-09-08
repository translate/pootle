# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json
from urlparse import parse_qs

import pytest

from pytest_pootle.search import calculate_search_results

from pootle.core.contextmanagers import keep_data
from pootle_app.models import Directory
from pootle_app.models.permissions import check_user_permission
from pootle_project.models import Project
from pootle_store.models import Unit


@pytest.mark.django_db
def test_get_units(get_units_views):
    (user, search_params, url_params, response) = get_units_views
    result = json.loads(response.content)

    path = parse_qs(url_params)["path"][0]

    permission_context = None
    if path.strip("/") in ["", "projects"]:
        permission_context = Directory.objects.get(pootle_path="/projects/")
    elif path.startswith("/projects/"):
        try:
            permission_context = Project.objects.get(
                code=path[10:].split("/")[0]).directory
        except Project.DoesNotExist:
            assert response.status_code == 404
            assert "unitGroups" not in result
            return

    user_cannot_view = (
        permission_context
        and not check_user_permission(
            user, "administrate", permission_context))
    if user_cannot_view:
        assert response.status_code == 404
        assert "unitGroups" not in result
        return

    assert "unitGroups" in result
    assert isinstance(result["unitGroups"], list)

    for k in "start", "end", "total":
        assert k in result
        assert isinstance(result[k], int)

    if result["unitGroups"]:
        total, start, end, expected_units = calculate_search_results(
            search_params, user)

        assert result["total"] == total
        assert result["start"] == start
        assert result["end"] == end

        for i, group in enumerate(expected_units):
            result_group = result["unitGroups"][i]
            for store, data in group.items():
                result_data = result_group[store]
                assert (
                    [u["id"] for u in result_data["units"]]
                    == [u["id"] for u in data["units"]])


@pytest.mark.django_db
def test_get_previous_slice(client, request_users):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    resp = client.get(
        "/xhr/units/?filter=all&count=5&path=/&offset=60",
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    if not request_users.get("is_superuser", False):
        assert resp.status_code == 404
        return

    result = json.loads(resp.content)
    qs = Unit.objects.get_translatable(
        user=resp.wsgi_request.user).order_by("store__pootle_path", "index")

    uids = []
    for group in result["unitGroups"]:
        for group_data in group.values():
            for unit in group_data["units"]:
                uids.append(unit["id"])

    assert result["start"] == 60
    assert result["end"] == 70
    assert result["total"] == qs.count()
    assert uids == list(qs[60:70].values_list("pk", flat=True))

    resp2 = client.get(
        "/xhr/units/",
        dict(
            filter="all",
            count=5,
            path="/",
            offset=50),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    result2 = json.loads(resp2.content)

    uids2 = []
    for group in result2["unitGroups"]:
        for group_data in group.values():
            for unit in group_data["units"]:
                uids2.append(unit["id"])

    assert result2["start"] == 50
    assert result2["end"] == 60
    assert result2["total"] == qs.count()
    assert uids2 == list(qs[50:60].values_list("pk", flat=True))

    expected = list(qs[40:50].values_list("pk", flat=True))

    to_obsolete = [uid for i, uid in enumerate(uids2) if i % 2]
    with keep_data():
        for unit in Unit.objects.filter(id__in=to_obsolete):
            unit.makeobsolete()
            unit.save()

    assert expected == list(qs.all()[40:50].values_list("pk", flat=True))

    resp3 = client.get(
        "/xhr/units/",
        dict(
            filter="all",
            count=5,
            path="/",
            offset=40),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    result3 = json.loads(resp3.content)

    uids3 = []
    for group in result3["unitGroups"]:
        for group_data in group.values():
            for unit in group_data["units"]:
                uids3.append(unit["id"])

    # obsoleting the units makes no difference when paginating backwards
    assert result3["start"] == 40
    assert result3["end"] == 50
    assert result3["total"] == qs.count()
    assert uids3 == list(
        qs[40:50].values_list("pk", flat=True))


@pytest.mark.django_db
def test_get_next_slice(client, request_users):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    resp = client.get(
        "/xhr/units/?filter=all&count=5&path=/",
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    if not request_users.get("is_superuser", False):
        assert resp.status_code == 404
        return

    result = json.loads(resp.content)

    qs = Unit.objects.get_translatable(
        user=resp.wsgi_request.user).order_by("store__pootle_path", "index")

    uids = []
    for group in result["unitGroups"]:
        for group_data in group.values():
            for unit in group_data["units"]:
                uids.append(unit["id"])

    assert result["start"] == 0
    assert result["end"] == 10
    assert result["total"] == qs.count()
    assert uids == list(qs[:10].values_list("pk", flat=True))

    resp2 = client.get(
        "/xhr/units/",
        dict(
            filter="all",
            count=5,
            path="/",
            offset=10,
            previous_uids=uids),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    result2 = json.loads(resp2.content)

    uids2 = []
    for group in result2["unitGroups"]:
        for group_data in group.values():
            for unit in group_data["units"]:
                uids2.append(unit["id"])

    assert result2["start"] == 10
    assert result2["end"] == 20
    assert result2["total"] == qs.count()
    assert uids2 == list(qs[10:20].values_list("pk", flat=True))

    expected = list(qs[20:30].values_list("pk", flat=True))

    to_obsolete = [uid for i, uid in enumerate(uids2) if i % 2]
    for unit in Unit.objects.filter(id__in=to_obsolete):
        unit.makeobsolete()
        unit.save()

    assert expected == list(qs.all()[15:25].values_list("pk", flat=True))

    resp3 = client.get(
        "/xhr/units/",
        dict(
            filter="all",
            count=5,
            path="/",
            offset=20,
            previous_uids=uids2),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

    result3 = json.loads(resp3.content)

    uids3 = []
    for group in result3["unitGroups"]:
        for group_data in group.values():
            for unit in group_data["units"]:
                uids3.append(unit["id"])

    assert result3["start"] == 20 - len(to_obsolete)
    assert result3["end"] == 30 - len(to_obsolete)
    assert result3["total"] == qs.count()

    start = 20 - len(to_obsolete)
    end = 30 - len(to_obsolete)

    assert uids3 == list(
        qs[start:end].values_list("pk", flat=True))

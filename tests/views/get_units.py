# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from pytest_pootle.search import calculate_search_results

from pootle_store.models import Unit


@pytest.mark.django_db
def test_get_units(get_units_views):
    (user, search_params, url_params, response) = get_units_views
    result = json.loads(response.content)

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
def test_get_previous_slice(client):
    import json
    resp = client.get(
        "/xhr/units/?filter=all&count=5&path=/&offset=60",
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

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
def test_get_next_slice(client):
    import json
    resp = client.get(
        "/xhr/units/?filter=all&count=5&path=/",
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')

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

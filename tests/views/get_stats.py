# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from pootle_store.models import Unit


@pytest.mark.django_db
def test_get_stats_store(client, request_users, settings):

    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    unit = Unit.objects.get_translatable(user).first()
    store = unit.store
    response = client.get(
        "/xhr/stats/?path=%s" % store.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    result = json.loads(response.content)

    stats = store.get_stats()
    for k, v in result.items():
        assert stats[k] == v
    assert "vfolders" not in result


@pytest.mark.django_db
def test_get_stats_directory(client, request_users, settings):

    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    unit = (
        Unit.objects.get_translatable(user)
                    .filter(store__pootle_path__contains="subdir0")
                    .first())
    directory = unit.store.parent
    response = client.get(
        "/xhr/stats/?path=%s" % directory.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    request = response.wsgi_request
    result = json.loads(response.content)

    stats = directory.get_stats()
    stats["vfolders"] = {}

    for vfolder_treeitem in directory.vf_treeitems.iterator():
        if request.user.is_superuser or vfolder_treeitem.is_visible:
            vfti_stats = vfolder_treeitem.get_stats(include_children=False)
            stats['vfolders'][str(vfolder_treeitem.code)] = vfti_stats

    for k, v in result.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                assert stats[k][kk] == vv
        else:
            assert stats[k] == v


@pytest.mark.django_db
def test_get_stats_tp(client, request_users, settings):

    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    unit = (
        Unit.objects.get_translatable(user)
                    .first())
    tp = unit.store.translation_project
    response = client.get(
        "/xhr/stats/?path=%s" % tp.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    result = json.loads(response.content)

    stats = tp.get_stats()

    for k, v in result.items():
        if isinstance(v, dict):
            for kk, vv in v.items():
                assert stats[k][kk] == vv
        else:
            assert stats[k] == v

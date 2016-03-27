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
def test_get_qc_stats_store(client, request_users, settings):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    unit = Unit.objects.get_translatable(user).first()
    store = unit.store
    response = client.get(
        "/xhr/stats/checks/?path=%s" % store.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    result = json.loads(response.content)
    checks = store.get_checks() or {}
    for k, v in result.items():
        assert checks[k] == v


@pytest.mark.django_db
def test_get_qc_stats_directory(client, request_users, settings):
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
        "/xhr/stats/checks/?path=%s" % directory.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    result = json.loads(response.content)
    checks = directory.get_checks() or {}
    for k, v in result.items():
        assert checks[k] == v


@pytest.mark.django_db
def test_get_qc_stats_tp(client, request_users, settings):
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
        "/xhr/stats/checks/?path=%s" % tp.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    result = json.loads(response.content)
    checks = tp.get_checks() or {}
    for k, v in result.items():
        assert checks[k] == v

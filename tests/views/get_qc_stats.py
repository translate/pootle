# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from pootle_app.models import Directory
from pootle_project.models import Project, ProjectResource, ProjectSet
from pootle_store.models import Store, Unit


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
    checks = store.data_tool.get_checks() or {}
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
    checks = directory.data_tool.get_checks() or {}
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
    checks = tp.data_tool.get_checks() or {}
    for k, v in result.items():
        assert checks[k] == v


@pytest.mark.django_db
def test_get_qc_stats_language(client, request_users, settings):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    unit = (
        Unit.objects.get_translatable(user)
                    .first())
    language = unit.store.translation_project.language
    response = client.get(
        "/xhr/stats/checks/?path=%s" % language.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    result = json.loads(response.content)
    checks = language.data_tool.get_checks() or {}
    for k, v in result.items():
        assert checks[k] == v


@pytest.mark.django_db
def test_get_qc_stats_projects(client, request_users, settings):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    user_projects = (
        Project.objects.for_user(user)
                       .select_related("directory"))
    project_set = ProjectSet(user_projects)
    response = client.get(
        "/xhr/stats/checks/?path=/projects/",
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    result = json.loads(response.content)
    checks = project_set.data_tool.get_checks() or {}
    for k, v in result.items():
        assert checks[k] == v


@pytest.mark.django_db
def test_get_qc_stats_project(client, request_users, settings):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    unit = (
        Unit.objects.get_translatable(user)
                    .first())
    project = unit.store.translation_project.project
    response = client.get(
        "/xhr/stats/checks/?path=/projects/%s/" % project.code,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    result = json.loads(response.content)
    checks = project.data_tool.get_checks() or {}
    for k, v in result.items():
        assert checks[k] == v


@pytest.mark.django_db
def test_get_qc_stats_project_dir(client, request_users, settings, subdir0):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    project = subdir0.tp.project
    dirs = Directory.objects.live().filter(tp__project=project)
    resources = (
        dirs.exclude(pootle_path__startswith="/templates")
            .filter(tp_path=subdir0.tp_path))
    resource_path = "/projects/%s%s" % (project.code, subdir0.tp_path)
    projectres = ProjectResource(resources, resource_path)
    response = client.get(
        "/xhr/stats/checks/?path=%s" % resource_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    result = json.loads(response.content)
    checks = projectres.data_tool.get_checks() or {}
    for k, v in result.items():
        assert checks[k] == v


@pytest.mark.django_db
def test_get_qc_stats_project_store(client, request_users, settings, subdir0):
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])
    store = subdir0.child_stores.first()
    project = subdir0.tp.project
    resources = (
        Store.objects.live()
                     .select_related("translation_project__language")
                     .filter(translation_project__project=project)
                     .filter(tp_path=store.tp_path))
    resource_path = "/projects/%s%s" % (project.code, store.tp_path)
    projectres = ProjectResource(resources, resource_path)
    response = client.get(
        "/xhr/stats/checks/?path=%s" % resource_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    result = json.loads(response.content)
    checks = projectres.data_tool.get_checks() or {}
    for k, v in result.items():
        assert checks[k] == v

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from pootle.core.delegate import scores
from pootle_app.models.directory import Directory
from pootle_language.models import Language
from pootle_project.models import Project, ProjectSet
from pootle_store.models import Store
from pootle_translationproject.models import TranslationProject

from pootle.core.utils.stats import TOP_CONTRIBUTORS_CHUNK_SIZE


def get_top_scorers_test_data(obj, offset=0):
    score_data = scores.get(obj.__class__)(obj)
    chunk_size = TOP_CONTRIBUTORS_CHUNK_SIZE

    def scores_to_json(score):
        score["user"] = score["user"].to_dict()
        return score
    top_scorers = score_data.display(
        offset=offset,
        limit=chunk_size,
        formatter=scores_to_json)
    return dict(
        items=list(top_scorers),
        has_more_items=len(score_data.top_scorers) > (offset + chunk_size))


@pytest.mark.django_db
def test_get_contributors_store(client, request_users):

    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    store = Store.objects.get(pootle_path="/language0/project0/store0.po")
    response = client.get(
        "/xhr/stats/contributors/?path=%s" % store.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    result = json.loads(response.content)
    top_scorers_data = get_top_scorers_test_data(store.translation_project)
    for k, v in result.items():
        assert json.loads(json.dumps(top_scorers_data[k])) == v


@pytest.mark.django_db
def test_get_contributors_tp(client, request_users):

    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    tp = TranslationProject.objects.get(pootle_path="/language0/project0/")
    response = client.get(
        "/xhr/stats/contributors/?path=%s" % tp.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    result = json.loads(response.content)

    top_scorers_data = get_top_scorers_test_data(tp)
    for k, v in result.items():
        assert json.loads(json.dumps(top_scorers_data[k])) == v


@pytest.mark.django_db
def test_get_contributors_project(client, request_users):

    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    project = Project.objects.get(code="project0")
    response = client.get(
        "/xhr/stats/contributors/?path=%s" % project.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    result = json.loads(response.content)

    top_scorers_data = get_top_scorers_test_data(project)
    for k, v in result.items():
        assert json.loads(json.dumps(top_scorers_data[k])) == v


@pytest.mark.django_db
def test_get_contributors_language(client, request_users):

    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    language = Language.objects.get(code="language0")
    response = client.get(
        "/xhr/stats/contributors/?path=%s" % language.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    result = json.loads(response.content)

    top_scorers_data = get_top_scorers_test_data(language)
    for k, v in result.items():
        assert json.loads(json.dumps(top_scorers_data[k])) == v


@pytest.mark.django_db
def test_get_contributors_projects_offset(client, request_users):
    offset = 3
    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    directory = Directory.objects.projects
    response = client.get(
        ("/xhr/stats/contributors/?path=%s&offset=%d"
         % (directory.pootle_path, offset)),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    result = json.loads(response.content)
    user_projects = Project.accessible_by_user(user)
    user_projects = (
        Project.objects.for_user(user)
                       .filter(code__in=user_projects))
    top_scorers_data = get_top_scorers_test_data(
        ProjectSet(user_projects),
        offset=offset)
    for k, v in result.items():
        assert json.loads(json.dumps(top_scorers_data[k])) == v


@pytest.mark.django_db
def test_get_contributors_projects(client, request_users):

    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    directory = Directory.objects.projects
    response = client.get(
        "/xhr/stats/contributors/?path=%s" % directory.pootle_path,
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 200
    result = json.loads(response.content)
    user_projects = Project.accessible_by_user(user)
    user_projects = (
        Project.objects.for_user(user)
                       .filter(code__in=user_projects))
    top_scorers_data = get_top_scorers_test_data(ProjectSet(user_projects))
    for k, v in result.items():
        assert json.loads(json.dumps(top_scorers_data[k])) == v


@pytest.mark.parametrize('path, offset', [
    ("/TOO_LONG_PATH" * 200, 0),
    ("/language0/", 'WRONG_OFFSET'),
])
@pytest.mark.django_db
def test_get_contributors_wrong_params(client, request_users, path, offset):

    user = request_users["user"]
    if user.username != "nobody":
        client.login(
            username=user.username,
            password=request_users["password"])

    response = client.get(
        "/xhr/stats/contributors/?path=%s&offset=%s" % (path, offset),
        HTTP_X_REQUESTED_WITH='XMLHttpRequest')
    assert response.status_code == 404

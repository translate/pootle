# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from django.utils.translation import get_language
from django.urls import reverse

from pootle.core.decorators import Http400
from pootle.core.debug import memusage
from pootle.core.delegate import revision
from pootle_app.views.index.index import (
    COOKIE_NAME, IndexView, WelcomeView)
from pootle_language.models import Language
from pootle_score.display import TopScoreDisplay
from pootle_translationproject.models import TranslationProject


@pytest.mark.django_db
def test_view_index(client, rf, request_users, language0):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get("")
    if not user.is_authenticated:
        assert response.status_code == 200
        assert isinstance(response.context["view"], WelcomeView)
    else:
        assert response.status_code == 302
        assert response["Location"] == reverse("pootle-projects-browse")

    request = rf.get("")
    request.user = user
    request.COOKIES[COOKIE_NAME] = language0.code
    response = IndexView.as_view()(request=request)
    if not user.is_authenticated:
        assert response.status_code == 200
    else:
        assert response.status_code == 302
        assert response["Location"] == reverse(
            "pootle-language-browse",
            kwargs=dict(language_code=language0.code))


@pytest.mark.django_db
def test_view_welcome(client, member, system, project_set):
    response = client.get(reverse('pootle-home'))
    assert isinstance(response.context["score_data"], TopScoreDisplay)
    assert isinstance(response.context["view"], WelcomeView)
    assert response.context["view"].request_lang == get_language()
    assert (
        response.context["view"].project_set.directory
        == project_set.directory)
    assert (
        response.context["view"].revision
        == revision.get(project_set.directory.__class__)(
            project_set.directory).get(key="stats"))
    assert (
        response.context["view"].cache_key
        == (
            "%s.%s.%s"
            % (response.wsgi_request.user.username,
               response.context["view"].revision,
               get_language())))


@pytest.mark.pootle_memusage
@pytest.mark.django_db
def test_view_welcome_garbage(client):
    url = reverse("pootle-home")
    response = client.get(url)
    response = client.get(url)
    assert response.status_code == 200
    for i in xrange(0, 2):
        with memusage() as usage:
            client.get(url)
        assert not usage["used"]


@pytest.mark.django_db
def test_view_index_redirect(client, language0, project0, request_users):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get("/")
    if user.is_authenticated:
        assert response.status_code == 302
        assert response.url == "/projects/"
    else:
        assert response.status_code == 200

    # cookie test
    client.cookies["pootle-language"] = language0.code
    response = client.get("/")
    if user.is_authenticated:
        assert response.status_code == 302
        assert response.url == "/%s/" % language0.code
    else:
        assert response.status_code == 200

    # accept lang test
    del client.cookies["pootle-language"]
    es = Language.objects.create(code="es")
    TranslationProject.objects.create(language=es, project=project0)
    response = client.get("/", HTTP_ACCEPT_LANGUAGE="es")
    if user.is_authenticated:
        assert response.status_code == 302
        assert response.url == "/es/"
    else:
        assert response.status_code == 200


@pytest.mark.django_db
def test_view_user_permissions_json(client, request_users, project0,
                                    member, member2):
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(
        reverse(
            'pootle-permissions-users',
            kwargs=dict(directory=project0.directory.pk)))
    if not user.is_superuser:
        assert response.status_code == 403
        return
    result = json.loads(response.content)
    assert result["items"] == []
    with pytest.raises(Http400):
        client.post(
            reverse(
                'pootle-permissions-users',
                kwargs=dict(directory=project0.directory.pk)))
    response = client.post(
        reverse(
            'pootle-permissions-users',
            kwargs=dict(directory=project0.directory.pk)),
        dict(q="mem"))
    results = json.loads(response.content)["items"]["results"]
    assert results[0]['text'] == member.username
    assert results[0]['id'] == member.pk
    assert results[1]['text'] == member2.username
    assert results[1]['id'] == member2.pk

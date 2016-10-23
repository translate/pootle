# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from django.core.urlresolvers import reverse

from pootle.core.delegate import language_team
from pootle_language.forms import LanguageTeamAdminForm


@pytest.mark.django_db
def test_view_language_team_new_member(client, language0, request_users,
                                       member, member2):
    user = request_users["user"]
    team = language_team.get(language0.__class__)(language0)
    admin_url = reverse(
        'pootle-language-admin-team-new-members',
        kwargs=dict(language_code=language0.code))
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(admin_url)
    if not user.is_superuser:
        assert response.status_code == 403
        if user.is_anonymous():
            return
        team.add_member(user, "admin")
        response = client.get(admin_url)
    assert json.loads(response.content)["items"] == []
    search_member = (
        member
        if user == member2
        else member2)
    response = client.get("%s?q=%s" % (admin_url, search_member.username[:2]))
    result = json.loads(response.content)
    assert search_member.username in [r["username"] for r in result["items"]]
    team = language_team.get(language0.__class__)(language0)
    team.add_member(search_member, "member")
    response = client.get("%s?q=%s" % (admin_url, search_member.username[:2]))
    result = json.loads(response.content)
    assert (
        search_member.username
        not in [r["username"] for r in result["items"]])
    if user in team.admins:
        team.remove_member(user)

    from django.core.cache import cache
    from django.utils.encoding import iri_to_uri
    key = iri_to_uri('Permissions:%s' % user.username)
    key = iri_to_uri('Permissions:%s' % search_member.username)
    cache.delete(key)


@pytest.mark.django_db
def test_view_language_team_admin(client, language0, request_users):
    user = request_users["user"]
    team = language_team.get(language0.__class__)(language0)
    admin_url = reverse(
        'pootle-language-admin-team',
        kwargs=dict(language_code=language0.code))
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(admin_url)
    if not user.is_superuser:
        assert response.status_code == 403
        if user.is_anonymous():
            return
        team.add_member(user, "admin")
        response = client.get(admin_url)
    assert isinstance(
        response.context["form"], LanguageTeamAdminForm)
    assert (
        list(response.context["tps"])
        == list(
            language0.translationproject_set.exclude(
                project__disabled=True)))
    assert (
        list(response.context["stats"])
        == list(
            language0.data_tool.get_stats(
                include_children=False,
                user=user)))
    assert (
        list(response.context["suggestions"])
        == list(
            response.context["form"].language_team.suggestions))
    assert response.context["language"] == language0
    if user in team.admins:
        team.remove_member(user)


@pytest.mark.django_db
def test_view_language_team_admin_post(client, language0, request_users,
                                       member, member2):
    user = request_users["user"]
    team = language_team.get(language0.__class__)(language0)
    search_member = (
        member
        if user == member2
        else member2)
    assert search_member not in team.members
    admin_url = reverse(
        'pootle-language-admin-team',
        kwargs=dict(language_code=language0.code))
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.post(
        admin_url,
        data=dict(new_member=search_member.id, role="member"))
    if not user.is_superuser:
        assert search_member not in team.members
        if user.is_anonymous():
            assert response.status_code == 402
            return
        team.add_member(user, "admin")
        response = client.post(
            admin_url,
            data=dict(new_member=search_member.id, role="member"))
    team.update_permissions()
    assert search_member in team.members
    assert response.status_code == 302
    response = client.post(
        admin_url,
        data=dict(rm_members=[search_member.id]))
    team.update_permissions()
    assert search_member not in team.members
    assert response.status_code == 302

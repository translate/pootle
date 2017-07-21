# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import json

import pytest

from django import forms
from django.urls import reverse

from pootle.core.browser import make_project_item
from pootle.core.debug import memusage
from pootle.core.delegate import language_team
from pootle.core.exceptions import Http400
from pootle.core.forms import FormtableForm
from pootle.core.views.browse import StatsDisplay
from pootle_language.forms import (
    LanguageSuggestionAdminForm, LanguageTeamAdminForm)
from pootle_language.views import (
    LanguageBrowseView, SuggestionDisplay, SuggestionFormtable)
from pootle_misc.util import cmp_by_last_activity
from pootle_store.constants import STATES_MAP
from pootle_store.models import Unit


class DummyFormtableForm(FormtableForm):
    search_field = "units"
    units = forms.ModelMultipleChoiceField(
        Unit.objects.order_by("id"),
        required=False)


def _test_view_language_children(view, obj):
    request = view.request

    user_tps = obj.get_children_for_user(request.user)
    stats = obj.data_tool.get_stats(user=request.user)
    items = [make_project_item(tp) for tp in user_tps]
    for item in items:
        if item["code"] in stats["children"]:
            item["stats"] = stats["children"][item["code"]]
    items.sort(cmp_by_last_activity)
    stats = StatsDisplay(obj, stats=stats).stats
    assert stats == view.stats
    assert view.object_children == items


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
    if not user.is_superuser:
        response = client.post(admin_url)
        assert response.status_code == 403
    else:
        with pytest.raises(Http400):
            client.post(admin_url)

    response = client.post(admin_url, data=dict(q="DOES NOT EXIST"))
    if not user.is_superuser:
        if user.is_anonymous:
            assert response.status_code == 402
            return
        assert response.status_code == 403
        team.add_member(user, "admin")
        response = client.post(admin_url, data=dict(q="DOES NOT EXIST"))
    assert json.loads(response.content)["items"]["results"] == []
    search_member = (
        member
        if user == member2
        else member2)
    response = client.post(admin_url, data=dict(q=search_member.username[:2]))
    result = json.loads(response.content)
    assert search_member.username in [r["text"] for r in result["items"]["results"]]
    team = language_team.get(language0.__class__)(language0)
    team.add_member(search_member, "member")
    response = client.post(admin_url, data=dict(q=search_member.username[:2]))
    result = json.loads(response.content)
    assert (
        search_member.username
        not in [r["text"] for r in result["items"]["results"]])
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
        if user.is_anonymous:
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
    for k in response.context["stats"].keys():
        if k.endswith("_display"):
            del response.context["stats"][k]
    assert (
        sorted(response.context["stats"])
        == sorted(
            language0.data_tool.get_stats(
                include_children=False,
                user=user)))
    assert (
        response.context["suggestions"]
        == response.context["form"].language_team.suggestions.count())
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
        if user.is_anonymous:
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


# TODO: move me to somewhere suggestion related
@pytest.mark.django_db
def test_display_language_suggestion(language0):
    team = language_team.get()(language0)
    suggestion = team.suggestions.first()
    display = SuggestionDisplay(suggestion)
    assert display.__suggestion__ is suggestion
    assert (
        display.project
        == ("<a href='%s'>%s</a>"
            % (suggestion.unit.store.translation_project.pootle_path,
               suggestion.unit.store.translation_project.project.code)))
    assert display.unit == display.__suggestion__.unit.source
    assert (
        display.unit_link
        == ("<a href='%s'>#%s</a>"
            % (suggestion.unit.get_translate_url(),
               suggestion.unit.id)))
    assert (
        str(display.unit_state)
        == STATES_MAP[suggestion.unit.state])
    assert (
        display.state
        == suggestion.state)

    with pytest.raises(AttributeError):
        display.DOES_NOT_EXIST


@pytest.mark.django_db
def test_formtable_language_team_suggestions(language0):
    formtable = SuggestionFormtable(DummyFormtableForm())
    assert formtable.row_field == "suggestions"
    assert (
        formtable.filters_template
        == "languages/admin/includes/suggestions_header.html")
    assert formtable.messages == []

    formtable = SuggestionFormtable(DummyFormtableForm(), messages=["FOO"])
    assert formtable.messages == ["FOO"]


@pytest.mark.django_db
def test_view_admin_language_team_suggestion(client, language0, request_users):
    user = request_users["user"]
    team = language_team.get(language0.__class__)(language0)
    admin_url = reverse(
        'pootle-language-admin-suggestions',
        kwargs=dict(language_code=language0.code))
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(admin_url)
    if not user.is_superuser:
        assert response.status_code == 403
        if user.is_anonymous:
            return
        team.add_member(user, "admin")
        response = client.get(admin_url)
    assert response.context["language"] == language0
    assert response.context["page"] == "admin-suggestions"
    formtable = response.context["formtable"]
    assert isinstance(formtable, SuggestionFormtable)
    assert isinstance(formtable.form, LanguageSuggestionAdminForm)
    assert formtable.form.user == response.wsgi_request.user
    assert formtable.form.language == language0
    assert formtable.form.data == dict(
        page_no=1,
        results_per_page=10)
    assert (
        [x[0] for x in formtable.form.fields["suggestions"].choices]
        == [item.id
            for item in
            formtable.form.batch().object_list])
    assert isinstance(
        formtable.form.fields["suggestions"].choices[0][1],
        SuggestionDisplay)


@pytest.mark.django_db
def test_view_admin_language_suggestion_post(client, language0, request_users,
                                             mailoutbox):
    user = request_users["user"]
    team = language_team.get(language0.__class__)(language0)
    admin_url = reverse(
        'pootle-language-admin-suggestions',
        kwargs=dict(language_code=language0.code))
    client.login(
        username=user.username,
        password=request_users["password"])
    suggestion = team.suggestions.first()
    data = dict(
        actions="accept",
        suggestions=[suggestion.id])
    response = client.post(admin_url, data=data)
    if not user.is_superuser:
        if user.is_anonymous:
            assert response.status_code == 402
            return
        assert response.status_code == 403
        team.add_member(user, "admin")
        response = client.post(admin_url, data=data)
    assert response.status_code == 302
    suggestion.refresh_from_db()
    assert suggestion.state.name == "accepted"
    assert len(mailoutbox) == 0

    # reject
    suggestion = team.suggestions.first()
    data = dict(
        actions="reject",
        suggestions=[suggestion.id])
    response = client.post(admin_url, data=data)
    assert response.status_code == 302
    suggestion.refresh_from_db()
    assert suggestion.state.name == "rejected"
    assert len(mailoutbox) == 0

    # reject with comment
    suggestion = team.suggestions.first()
    data = dict(
        actions="accept",
        comment="ta very much!",
        suggestions=[suggestion.id])
    response = client.post(admin_url, data=data)
    assert response.status_code == 302
    suggestion.refresh_from_db()
    assert suggestion.state.name == "accepted"
    assert len(mailoutbox) == 1

    # reject with comment
    suggestion = team.suggestions.first()
    data = dict(
        actions="reject",
        comment="no way!",
        suggestions=[suggestion.id])
    response = client.post(admin_url, data=data)
    assert response.status_code == 302
    suggestion.refresh_from_db()
    assert suggestion.state.name == "rejected"
    assert len(mailoutbox) == 2


@pytest.mark.django_db
def test_view_language_children(language0, rf, request_users):
    request = rf.get('/language0/')
    request.user = request_users["user"]
    view = LanguageBrowseView(
        kwargs=dict(
            language_code=language0.code))
    view.request = request
    view.object = view.get_object()
    assert view.object == language0
    _test_view_language_children(view, language0)


@pytest.mark.pootle_memusage
@pytest.mark.django_db
def test_view_language_garbage(language0, store0, client, request_users):
    url = reverse(
        "pootle-language-browse",
        kwargs=dict(
            language_code=language0.code))
    user = request_users["user"]
    client.login(
        username=user.username,
        password=request_users["password"])
    response = client.get(url)
    response = client.get(url)
    assert response.status_code == 200
    for i in xrange(0, 2):
        with memusage() as usage:
            client.get(url)
        assert not usage["used"]

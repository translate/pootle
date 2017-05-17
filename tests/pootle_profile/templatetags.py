# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from urllib import quote_plus

import pytest

from django.core.urlresolvers import reverse

from pootle.core.delegate import language_team, profile
from pootle.core.utils.templates import render_as_template


@pytest.mark.django_db
def test_templatetag_profile_ranking(member, rf, nobody):
    user_profile = profile.get(member.__class__)(member)
    request = rf.get("")
    request.user = nobody
    top_lang = user_profile.scores.top_language
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_ranking request profile %}",
        dict(profile=user_profile, request=request))
    assert (
        ("#%s contributor in %s in the last 30 days"
         % (top_lang[0], top_lang[1].name))
        in rendered)
    assert (
        quote_plus(
            "I am #%s contributor in %s in the last 30 days"
            % (top_lang[0], top_lang[1].name))
        not in rendered)
    request.user = member
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_ranking request profile %}",
        dict(profile=user_profile, request=request))
    assert (
        quote_plus(
            "I am #%s contributor in %s in the last 30 days"
            % (top_lang[0], top_lang[1].name))
        in rendered)
    nobody_profile = profile.get(nobody.__class__)(nobody)
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_ranking request profile %}",
        dict(profile=nobody_profile, request=request))
    assert "contributor in" not in rendered


@pytest.mark.django_db
def test_templatetag_profile_scores(member, rf, nobody, settings):
    user_profile = profile.get(member.__class__)(member)
    request = rf.get("")
    request.user = nobody
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_score request profile %}",
        dict(profile=user_profile, request=request))
    assert "Total score:" in rendered
    score = str(int(round(member.score)))
    assert score in rendered
    assert(
        quote_plus(
            "My current score at %s is %s"
            % (settings.POOTLE_TITLE, score))
        not in rendered)
    request.user = member
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_score request profile %}",
        dict(profile=user_profile, request=request))
    assert "Total score:" in rendered
    assert score in rendered
    assert(
        quote_plus(
            "My current score at %s is %s"
            % (settings.POOTLE_TITLE, score))
        in rendered)
    nobody_profile = profile.get(nobody.__class__)(nobody)
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_score request profile %}",
        dict(profile=nobody_profile, request=request))
    assert "0" in rendered
    assert (
        quote_plus("My current score at")
        not in rendered)


@pytest.mark.django_db
def test_templatetag_profile_social(member):
    user_profile = profile.get(member.__class__)(member)
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_social profile %}",
        dict(profile=user_profile))
    assert not rendered.strip()
    member.website = "http://foobar.baz"
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_social profile %}",
        dict(profile=user_profile))
    assert "My Website" in rendered
    assert "http://foobar.baz" in rendered
    member.twitter = "foomember"
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_social profile %}",
        dict(profile=user_profile))
    assert "@foomember" in rendered
    assert "https://twitter.com/foomember" in rendered
    member.linkedin = "https://linked.in/in/foomember"
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_social profile %}",
        dict(profile=user_profile))
    assert "My LinkedIn Profile" in rendered
    assert member.linkedin in rendered


@pytest.mark.django_db
def test_templatetag_profile_teams(rf, admin, member, language0, request_users):
    request_user = request_users["user"]
    lang_team = language_team.get()
    user_profile = profile.get(member.__class__)(member)
    request = rf.get("")
    request.user = request_user
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_teams request profile %}",
        dict(profile=user_profile, request=request))
    assert (
        ("%s is not a member of any language teams"
         % member.display_name)
        in rendered)
    lang_team(language0).add_member(member, "member")
    user_profile = profile.get(member.__class__)(member)
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_teams request profile %}",
        dict(profile=user_profile, request=request))
    assert language0.name in rendered
    lang_link = reverse(
        "pootle-language-browse",
        kwargs=dict(language_code=language0.code))
    assert lang_link in rendered
    assert ("/%s/" % lang_link) not in rendered
    assert "Admin" not in rendered
    assert "Site administrator" not in rendered
    lang_team(language0).add_member(member, "admin")
    user_profile = profile.get(member.__class__)(member)
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_teams request profile %}",
        dict(profile=user_profile, request=request))
    assert language0.name in rendered
    assert lang_link in rendered
    if request_user.is_anonymous:
        assert "Admin" not in rendered
    else:
        assert "Admin" in rendered
    admin_profile = profile.get(admin.__class__)(admin)
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_teams request profile %}",
        dict(profile=admin_profile, request=request))
    if request_user.is_anonymous:
        assert "Site administrator" not in rendered
    else:
        assert "Site administrator" in rendered


@pytest.mark.django_db
def test_templatetag_profile_user(member, rf, nobody, system, request_users):
    request_user = request_users["user"]
    member.email = "foo@bar.baz"
    user_profile = profile.get(member.__class__)(member)
    request = rf.get("")
    request.user = request_user
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_user request profile %}",
        dict(profile=user_profile, request=request))
    assert member.display_name in rendered
    if request_user.is_superuser:
        assert member.email in rendered
    else:
        assert member.email not in rendered
    if request_user == member:
        assert "Show others who you are" in rendered
        assert "js-user-profile-edit" in rendered
    else:
        assert "Show others who you are" not in rendered
        assert "js-user-profile-edit" not in rendered
    member.bio = "my life story"
    member.website = "http://foobar.baz"
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_user request profile %}",
        dict(profile=user_profile, request=request))
    assert "my life story" in rendered
    if request_user == member:
        assert "Show others who you are" not in rendered
        assert "js-user-profile-edit" in rendered
        assert "You can set or change your avatar" in rendered
    else:
        assert "Show others who you are" not in rendered
        assert "js-user-profile-edit" not in rendered
        assert "You can set or change your avatar" not in rendered
    nobody_profile = profile.get(nobody.__class__)(nobody)
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_user request profile %}",
        dict(profile=nobody_profile, request=request))
    assert "Show others who you are" not in rendered
    assert "js-user-profile-edit" not in rendered
    assert "Some translations are provided by anonymous volunteers" in rendered
    assert "You can set or change your avatar" not in rendered
    system_profile = profile.get(system.__class__)(system)
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_user request profile %}",
        dict(profile=system_profile, request=request))
    assert "Show others who you are" not in rendered
    assert "js-user-profile-edit" not in rendered
    assert "Some translations are imported from external files. " in rendered
    assert "You can set or change your avatar" not in rendered


@pytest.mark.django_db
def test_templatetag_profile_activity(member, rf, nobody, system, request_users):
    request_user = request_users["user"]
    user_profile = profile.get(member.__class__)(member)
    request = rf.get("")
    request.user = request_user
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_activity profile %}",
        dict(profile=user_profile))
    last_event = member.last_event()
    assert last_event.message in rendered
    assert "user-last-activity" in rendered

    nobody_profile = profile.get(nobody.__class__)(nobody)
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_activity profile %}",
        dict(profile=nobody_profile))
    assert "user-last-activity" not in rendered

    system_profile = profile.get(system.__class__)(system)
    rendered = render_as_template(
        "{% load profile_tags %}{% profile_activity profile %}",
        dict(profile=system_profile))
    assert "user-last-activity" not in rendered

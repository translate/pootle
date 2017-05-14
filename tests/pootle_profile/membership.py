# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import language_team, membership
from pootle_profile.utils import UserMembership


@pytest.mark.django_db
def test_membership_user(member, member2, language0, language1):
    lang_team = language_team.get()
    user_member = membership.get(member.__class__)(member)
    assert isinstance(user_member, UserMembership)
    assert user_member.user == member
    assert user_member.teams == []
    assert user_member.teams_and_roles == {}

    lang_team(language0).add_member(member, "admin")
    user_member = membership.get(member.__class__)(member)
    assert user_member.teams == [language0.code]
    assert user_member.teams_and_permissions == {
        language0.code: set(['administrate', 'review', 'suggest', 'translate'])}
    user_member.teams_and_roles[language0.code]["role"] == "Admin"
    user_member.teams_and_roles[language0.code]["name"] == language0.name

    lang_team(language1).add_member(member, "submitter")
    user_member = membership.get(member.__class__)(member)
    assert sorted(user_member.teams) == [language0.code, language1.code]
    assert user_member.teams_and_permissions == {
        language0.code: set(['administrate', 'review', 'suggest', 'translate']),
        language1.code: set(['suggest', 'translate'])}
    user_member.teams_and_roles[language0.code]["role"] == "Admin"
    user_member.teams_and_roles[language0.code]["name"] == language0.name
    user_member.teams_and_roles[language1.code]["role"] == "Translater"
    user_member.teams_and_roles[language1.code]["name"] == language1.name

    lang_team(language0).add_member(member2, "reviewer")
    user_member = membership.get(member2.__class__)(member2)
    assert user_member.teams == [language0.code]
    assert user_member.teams_and_permissions == {
        language0.code: set(['review', 'suggest', 'translate'])}
    user_member.teams_and_roles[language0.code]["role"] == "Reviewer"
    user_member.teams_and_roles[language0.code]["name"] == language0.name

    lang_team(language1).add_member(member2, "member")
    user_member = membership.get(member2.__class__)(member2)
    assert sorted(user_member.teams) == [language0.code, language1.code]
    assert user_member.teams_and_permissions == {
        language0.code: set(['review', 'suggest', 'translate']),
        language1.code: set(['suggest'])}
    user_member.teams_and_roles[language0.code]["role"] == "Reviewer"
    user_member.teams_and_roles[language0.code]["name"] == language0.name
    user_member.teams_and_roles[language1.code]["role"] == ""
    user_member.teams_and_roles[language1.code]["name"] == language1.name

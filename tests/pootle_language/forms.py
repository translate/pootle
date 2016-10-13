# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.urlresolvers import reverse

from pootle_language.forms import (
    LanguageTeamAdminForm, LanguageTeamNewMemberSearchForm)
from pootle_language.teams import LanguageTeam


@pytest.mark.django_db
def test_form_language_team_new_member(language0, member):
    form = LanguageTeamNewMemberSearchForm(language=language0)
    assert isinstance(form.language_team, LanguageTeam)
    form = LanguageTeamNewMemberSearchForm(
        language=language0,
        data=dict(q=member.username[:2]))
    assert form.is_valid()
    assert (
        dict(username=member.username, id=member.id)
        in form.search())
    form.language_team.add_member(member, "member")
    assert (
        dict(username=member.username, id=member.id)
        not in form.search())


@pytest.mark.django_db
def test_form_language_admin(language0, member, member2):
    form = LanguageTeamAdminForm(language=language0)
    assert form.language == language0
    assert isinstance(form.language_team, LanguageTeam)
    for role in form.language_team.roles:
        assert(
            list(form.fields["rm_%ss" % role].queryset.values_list("id", flat=True))
            == list(getattr(form.language_team, "%ss" % role)))
    assert (
        form.fields["new_member"].widget.attrs["data-select2-url"]
        == reverse(
            "pootle-language-admin-team-new-members",
            kwargs=dict(language_code=language0.code)))
    assert (
        list(form.fields["new_member"].queryset.values_list("id", flat=True))
        == list(form.language_team.non_members.values_list("id", flat=True)))

    # add a team member
    assert member not in form.language_team.members
    form = LanguageTeamAdminForm(
        language=language0,
        data=dict(new_member=member.id, role="member"))
    assert form.is_valid()
    form.save()
    assert member in form.language_team.members

    # add another team member
    assert member2 not in form.language_team.members
    form = LanguageTeamAdminForm(
        language=language0,
        data=dict(new_member=member2.id, role="member"))
    assert form.is_valid()
    form.save()
    assert member in form.language_team.members
    assert member2 in form.language_team.members

    # remove the first
    form = LanguageTeamAdminForm(
        language=language0,
        data=dict(rm_members=[member.pk]))
    assert form.is_valid()
    form.save()
    assert member not in form.language_team.members

    # adding takes priority
    form = LanguageTeamAdminForm(
        language=language0,
        data=dict(
            new_member=member.id,
            role="reviewer",
            rm_members=[member2.id]))
    assert form.is_valid()
    form.save()
    assert member in form.language_team.reviewers
    assert member2 in form.language_team.members


@pytest.mark.django_db
def test_form_language_admin_bad(language0, member):
    form = LanguageTeamAdminForm(
        language=language0,
        data=dict(new_member="DOES NOT EXIST", role="member"))
    assert not form.is_valid()
    assert form.errors["new_member"]
    form = LanguageTeamAdminForm(
        language=language0,
        data=dict(new_member=member.id))
    assert form.errors["role"]

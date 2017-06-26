# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.urls import reverse

from pootle.i18n.gettext import ugettext_lazy as _
from pootle_language.forms import (
    LanguageSuggestionAdminForm,
    LanguageTeamAdminForm, LanguageTeamNewMemberSearchForm)
from pootle_language.teams import LanguageTeam
from pootle_store.constants import FUZZY, OBSOLETE


@pytest.mark.django_db
def test_form_language_team_new_member(language0, member):
    form = LanguageTeamNewMemberSearchForm(language=language0)
    assert isinstance(form.language_team, LanguageTeam)
    form = LanguageTeamNewMemberSearchForm(
        language=language0,
        data=dict(q=member.username[:2]))
    assert form.is_valid()
    assert (
        dict(text=member.username, id=member.id)
        in form.search()["results"])
    form.language_team.add_member(member, "member")
    assert (
        dict(text=member.username, id=member.id)
        not in form.search()["results"])


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


@pytest.mark.django_db
def test_form_language_suggestions(language0, admin):
    form = LanguageSuggestionAdminForm(
        language=language0, user=admin)
    suggesters = list(
        (username,
         ("%s (%s)" % (fullname, username)
          if fullname.strip()
          else username))
        for username, fullname
        in sorted(form.language_team.users_with_suggestions))
    assert (
        form.filter_suggester_choices
        == [("", "-----")] + suggesters)
    suggestions = form.language_team.suggestions.filter(
        unit__store__translation_project__project__disabled=False,
        unit__store__obsolete=False)
    assert (
        list(form.suggestions_qs.values_list("id", flat=True))
        == list(
            suggestions.values_list("id", flat=True)))
    tps = form.language.translationproject_set.exclude(
        project__disabled=True)
    tps = tps.filter(
        stores__unit__suggestion__state__name="pending")
    assert (
        list(form.filter_tp_qs.values_list("id"))
        == list(tps.order_by("project__code").distinct().values_list("id")))
    assert (
        list(form.fields["filter_suggester"].choices)
        == list(form.filter_suggester_choices))
    assert (
        list(form.fields["filter_tp"].queryset)
        == list(form.filter_tp_qs))
    assert (
        list(form.fields["suggestions"].queryset)
        == list(form.suggestions_qs))
    assert (
        form.fields["actions"].choices
        == [("", "----"),
            ("reject", _("Reject")),
            ("accept", _("Accept"))])


@pytest.mark.django_db
def test_form_language_suggestions_save(language0, admin):
    form = LanguageSuggestionAdminForm(
        language=language0,
        user=admin)
    suggestions = form.language_team.suggestions[:3]
    form = LanguageSuggestionAdminForm(
        language=language0,
        user=admin,
        data=dict(
            actions="accept",
            suggestions=list(
                suggestions.values_list(
                    "id", flat=True))))
    assert form.is_valid()
    assert (
        list(form.suggestions_to_save)
        == list(suggestions))
    form.save()
    for suggestion in form.suggestions_to_save:
        assert suggestion.state.name == "accepted"


@pytest.mark.django_db
def test_form_language_suggestions_save_all(language0, tp0, admin):
    form = LanguageSuggestionAdminForm(
        language=language0,
        user=admin,
        data=dict(
            actions="reject",
            select_all=True,
            filter_tp=tp0.id))
    assert (
        list(form.suggestions_to_save)
        == list(
            form.language_team.suggestions.filter(
                unit__store__translation_project=tp0)))
    form.save()
    for suggestion in form.suggestions_to_save:
        assert suggestion.state.name == "rejected"


@pytest.mark.django_db
def test_form_language_suggestions_search(language0, tp0, admin):
    form = LanguageSuggestionAdminForm(language=language0, user=admin)
    team = form.language_team
    suggester = team.users_with_suggestions.pop()[0]
    suggestions = form.language_team.suggestions.filter(
        unit__store__translation_project__project__disabled=False,
        unit__store__obsolete=False)
    form = LanguageSuggestionAdminForm(
        language=language0,
        user=admin,
        data=dict(filter_suggester=suggester))
    assert form.is_valid()
    assert (
        list(form.search())
        == list(suggestions.filter(user__username=suggester)))
    form = LanguageSuggestionAdminForm(
        language=language0,
        user=admin,
        data=dict(filter_tp=tp0.id))
    assert form.is_valid()
    assert (
        list(form.search())
        == list(suggestions.filter(unit__store__translation_project=tp0)))
    form = LanguageSuggestionAdminForm(
        language=language0,
        user=admin,
        data=dict(filter_state=FUZZY))
    assert form.is_valid()
    assert (
        list(form.search())
        == list(suggestions.filter(unit__state=FUZZY)))


@pytest.mark.django_db
def test_form_language_suggestions_bad(language0, tp0, admin):
    with pytest.raises(KeyError):
        LanguageSuggestionAdminForm(language=language0)
    with pytest.raises(KeyError):
        LanguageSuggestionAdminForm(user=admin)
    form = LanguageSuggestionAdminForm(
        language=language0,
        user=admin,
        data=dict(filter_tp=tp0.id, filter_state=OBSOLETE))
    assert not form.is_valid()
    assert (
        list(form.batch().paginator.object_list)
        == list(
            form.language_team.suggestions.filter(
                unit__store__translation_project=tp0)))
    assert not form.suggestions_review
    assert not form.suggestions_to_save


@pytest.mark.django_db
def test_form_language_suggestions_accept_comment(language0, tp0, admin,
                                                  member2_with_email,
                                                  mailoutbox):
    form = LanguageSuggestionAdminForm(
        language=language0,
        user=admin,
        data=dict(
            actions="accept",
            comment="no thanks",
            select_all=True,
            filter_tp=tp0.id))
    assert (
        list(form.suggestions_to_save)
        == list(
            form.language_team.suggestions.filter(
                unit__store__translation_project=tp0)))
    form.save()
    for suggestion in form.suggestions_to_save:
        assert suggestion.state.name == "accepted"
    assert len(mailoutbox) == 1
    for suggestion in form.suggestions_to_save:
        assert ("#%s" % suggestion.id) in mailoutbox[0].body
    assert "accept" in mailoutbox[0].subject.lower()


@pytest.mark.django_db
def test_form_language_suggestions_reject_comment(language0, tp0, admin,
                                                  member2_with_email,
                                                  mailoutbox):
    form = LanguageSuggestionAdminForm(
        language=language0,
        user=admin,
        data=dict(
            actions="reject",
            comment="no thanks",
            select_all=True,
            filter_tp=tp0.id))
    assert (
        list(form.suggestions_to_save)
        == list(
            form.language_team.suggestions.filter(
                unit__store__translation_project=tp0)))
    form.save()
    for suggestion in form.suggestions_to_save:
        assert suggestion.state.name == "rejected"
    assert len(mailoutbox) == 1
    for suggestion in form.suggestions_to_save:
        assert ("#%s" % suggestion.id) in mailoutbox[0].body
    assert "reject" in mailoutbox[0].subject.lower()

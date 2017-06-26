# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.contrib.auth import get_user_model

from pootle.core.delegate import language_team
from pootle_language.models import Language
from pootle_language.teams import LanguageTeam
from pootle_store.constants import OBSOLETE
from pootle_store.models import Suggestion


@pytest.mark.django_db
def test_language_team_getter(language0):
    team = language_team.get(Language)(language0)
    assert isinstance(team, LanguageTeam)


@pytest.mark.django_db
def test_language_team_members(language0, member):
    team = language_team.get(Language)(language0)
    assert (
        list(team.members)
        == list(team.submitters)
        == list(team.reviewers)
        == list(team.admins)
        == [])
    team.add_member(member, "member")
    assert list(team.members) == [member]
    assert (
        list(team.submitters)
        == list(team.reviewers)
        == list(team.admins)
        == [])
    assert (
        member.permissionset_set
              .filter(directory=language0.directory)
              .filter(positive_permissions__codename="suggest")
              .count()
        == 1)
    assert (
        member.permissionset_set
              .filter(directory=language0.directory)
              .exclude(positive_permissions__codename="suggest")
              .count()
        == 0)
    team.add_member(member, "submitter")
    assert list(team.submitters) == [member]
    assert (
        list(team.members)
        == list(team.reviewers)
        == list(team.admins)
        == [])
    assert (
        member.permissionset_set
              .filter(directory=language0.directory)
              .filter(positive_permissions__codename__in=["suggest",
                                                          "translate"])
              .count()
        == 2)
    assert (
        member.permissionset_set
              .filter(directory=language0.directory)
              .exclude(positive_permissions__codename__in=["suggest",
                                                           "translate"])
              .count()
        == 0)
    team.add_member(member, "reviewer")
    assert list(team.reviewers) == [member]
    assert (
        list(team.members)
        == list(team.submitters)
        == list(team.admins)
        == [])
    assert (
        member.permissionset_set
              .filter(directory=language0.directory)
              .filter(positive_permissions__codename__in=["suggest",
                                                          "review",
                                                          "translate"])
              .count()
        == 3)
    assert (
        member.permissionset_set
              .filter(directory=language0.directory)
              .exclude(positive_permissions__codename__in=["suggest",
                                                           "review",
                                                           "translate"])
              .count()
        == 0)
    team.add_member(member, "admin")
    assert list(team.admins) == [member]
    assert (
        list(team.members)
        == list(team.submitters)
        == list(team.reviewers)
        == [])
    assert (
        member.permissionset_set
              .filter(directory=language0.directory)
              .filter(positive_permissions__codename__in=["suggest",
                                                          "review",
                                                          "administrate",
                                                          "translate"])
              .count()
        == 4)
    assert (
        member.permissionset_set
              .filter(directory=language0.directory)
              .exclude(positive_permissions__codename__in=["suggest",
                                                           "review",
                                                           "administrate",
                                                           "translate"])
              .count()
        == 0)
    team.remove_member(member)
    assert (
        list(team.members)
        == list(team.submitters)
        == list(team.reviewers)
        == list(team.admins)
        == [])
    assert (
        member.permissionset_set
              .filter(directory=language0.directory)
              .filter(positive_permissions__codename__in=["suggest",
                                                          "review",
                                                          "administrate",
                                                          "translate"])
              .count()
        == 0)


@pytest.mark.django_db
def test_language_team_non_members(language0, member):
    team = language_team.get(Language)(language0)
    team.add_member(member, "member")
    User = get_user_model()
    assert (
        sorted(team.non_members.values_list("id", flat=True))
        == sorted(
            User.objects.exclude(
                username=member.username).values_list("id", flat=True)))


@pytest.mark.django_db
def test_language_team_suggestions(language0):
    team = language_team.get(Language)(language0)
    suggestions = (
        Suggestion.objects.filter(
            state__name="pending",
            unit__state__gt=OBSOLETE,
            unit__store__translation_project__language=language0
        ).exclude(
            unit__store__translation_project__project__disabled=True
        ).exclude(unit__store__obsolete=True))
    assert (
        list(team.suggestions)
        == list(suggestions.order_by("-creation_time", "-pk")))
    # there should be some suggestions in the env
    assert team.suggestions
    assert (
        team.users_with_suggestions
        == set(
            team.suggestions.values_list(
                "user__username",
                "user__full_name")))

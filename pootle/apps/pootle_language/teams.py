# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from django.utils.functional import cached_property

from pootle_store.constants import OBSOLETE
from pootle_store.models import Suggestion


User = get_user_model()


class LanguageTeam(object):
    # this shouldnt be a dict
    roles = dict(
        member=["suggest"],
        submitter=["suggest", "translate"],
        reviewer=["suggest", "translate", "review"],
        admin=["administrate", "suggest", "translate", "review"])

    def __init__(self, language):
        self.language = language

    @property
    def admins(self):
        return self._get_members("administrate")

    @property
    def members(self):
        return self._get_members("suggest", ["translate", "review", "administrate"])

    @property
    def submitters(self):
        return self._get_members("translate", ["review", "administrate"])

    @property
    def reviewers(self):
        return self._get_members("review", ["administrate"])

    def add_member(self, user, role):
        permission_set = self.get_permission_set(user, create=True)
        for permission in self.get_permissions_for_role(role):
            permission_set.positive_permissions.add(permission)
        self.update_permissions()

    def get_permissions_for_role(self, role):
        return Permission.objects.filter(codename__in=self.roles[role])

    def get_permission_set(self, user, create=False):
        if create:
            return (
                self.language.directory.permission_sets.get_or_create(
                    user=user, directory=self.language.directory.id))[0]
        return self.language.directory.permission_sets.get(
            user=user, directory=self.language.directory.id)

    def remove_member(self, user):
        self.get_permission_set(user).delete()
        self.update_permissions()

    @property
    def non_members(self):
        return User.objects.exclude(
            pk__in=self._get_members("suggest").values_list("id", flat=True))

    @property
    def suggestions(self):
        suggestions = Suggestion.objects.filter(
            state__name="pending",
            unit__state__gt=OBSOLETE,
            unit__store__translation_project__language=self.language)
        suggestions = suggestions.exclude(
            unit__store__translation_project__project__disabled=True
        ).exclude(unit__store__obsolete=True)
        suggestions = suggestions.select_related(
            "unit",
            "unit__store",
            "unit__store__translation_project",
            "unit__store__translation_project__project")
        return suggestions.order_by("-creation_time", "-pk")

    @property
    def users_with_suggestions(self):
        return set(
            self.suggestions.values_list(
                "user__username",
                "user__full_name"))

    @property
    def superusers(self):
        return User.objects.filter(is_superuser=True)

    @cached_property
    def permissions(self):
        return self.language.directory.permission_sets.values_list(
            "positive_permissions__codename",
            "user")

    def _get_members(self, perm=None, exclude_perms=()):
        members = set()
        not_members = set()
        for (permission, user) in self.permissions:
            if permission == perm:
                members.add(user)
            if permission in exclude_perms:
                not_members.add(user)
        return User.objects.filter(
            pk__in=members - not_members).order_by("username")

    def update_permissions(self):
        if "permissions" in self.__dict__:
            del self.__dict__["permissions"]

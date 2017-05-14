# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from datetime import timedelta

from django.utils import timezone
from django.utils.functional import cached_property

from pootle.core.delegate import (
    comparable_event, log, membership, scores, site_languages)
from pootle.core.utils.templates import render_as_template
from pootle.i18n.gettext import ugettext_lazy as _


class UserProfile(object):

    def __init__(self, user):
        self.user = user

    @cached_property
    def avatar(self):
        return render_as_template(
            "{% load common_tags %}{% avatar username email_hash 20 %}",
            context=dict(
                username=self.user.username,
                email_hash=self.user.email_hash))

    @cached_property
    def log(self):
        return log.get(self.user.__class__)(self.user)

    @cached_property
    def membership(self):
        return membership.get(self.user.__class__)(self.user)

    @cached_property
    def scores(self):
        return scores.get(self.user.__class__)(self.user)

    @property
    def display_name(self):
        return (
            self.user.display_name
            if not self.user.is_anonymous
            else _("Anonymous User"))

    def get_events(self, start=None, n=None):
        sortable = comparable_event.get(self.log.__class__)
        start = start or (timezone.now() - timedelta(days=30))
        events = sorted(
            sortable(ev)
            for ev
            in self.log.get_events(start=start))
        if n is not None:
            events = events[-n:]
        return reversed(events)


class UserMembership(object):

    def __init__(self, user):
        self.user = user

    @cached_property
    def language_dirs(self):
        return dict(
            self.site_languages.site_languages.values_list(
                "directory", "code"))

    @cached_property
    def site_languages(self):
        return site_languages.get()

    @cached_property
    def teams_and_permissions(self):
        permsets = self.get_permission_set().values_list(
            "directory", "positive_permissions__codename")
        _teams = {}
        for lang, perm in permsets:
            lang = self.language_dirs.get(lang)
            _teams[lang] = _teams.get(lang, set())
            _teams[lang].add(perm)
        return _teams

    @cached_property
    def teams_and_roles(self):
        teams = {}
        for team, permissions in self.teams_and_permissions.items():
            teams[team] = dict(name=self.site_languages.languages[team])
            if "administrate" in permissions:
                teams[team]["role"] = _("Admin")
            elif "review" in permissions:
                teams[team]["role"] = _("Reviewer")
            elif "translate" in permissions:
                teams[team]["role"] = _("Translator")
            else:
                teams[team]["role"] = ""
        return teams

    @property
    def teams(self):
        return self.teams_and_permissions.keys()

    def get_permission_set(self):
        return self.user.permissionset_set.filter(
            directory_id__in=self.language_dirs.keys())

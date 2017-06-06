# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from .views import (
    LanguageBrowseView, LanguageSuggestionAdminView, LanguageTeamAdminFormView,
    LanguageTeamAdminNewMembersJSON, LanguageTranslateView,
    language_characters_admin)


urlpatterns = [
    url(r'^(?P<language_code>[^/]*)/$',
        LanguageBrowseView.as_view(),
        name='pootle-language-browse'),

    url(r'^(?P<language_code>[^/]*)/translate/$',
        LanguageTranslateView.as_view(),
        name='pootle-language-translate'),

    # Admin
    url(r'^(?P<language_code>[^/]*)/admin/team/$',
        LanguageTeamAdminFormView.as_view(),
        name='pootle-language-admin-team'),
    url(r'^(?P<language_code>[^/]*)/admin/team/new_members/$',
        LanguageTeamAdminNewMembersJSON.as_view(),
        name='pootle-language-admin-team-new-members'),
    url(r'(?P<language_code>[^/]*)/admin/suggestions/',
        LanguageSuggestionAdminView.as_view(),
        name='pootle-language-admin-suggestions'),
    url(r'^(?P<language_code>[^/]*)/admin/characters/$',
        language_characters_admin,
        name='pootle-language-admin-characters')]

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from .views import (
    LanguageBrowseView, LanguageExportView, LanguageTranslateView,
    language_admin, language_characters_admin)


urlpatterns = [
    url(r'^(?P<language_code>[^/]*)/$',
        LanguageBrowseView.as_view(),
        name='pootle-language-browse'),

    url(r'^(?P<language_code>[^/]*)/translate/$',
        LanguageTranslateView.as_view(),
        name='pootle-language-translate'),

    url(r'^(?P<language_code>[^/]*)/export-view/$',
        LanguageExportView.as_view(),
        name='pootle-language-export'),

    # Admin
    url(r'^(?P<language_code>[^/]*)/admin/permissions/$',
        language_admin,
        name='pootle-language-admin-permissions'),
    url(r'^(?P<language_code>[^/]*)/admin/characters/$',
        language_characters_admin,
        name='pootle-language-admin-characters'),
]

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import include, url

import staticpages.urls

from . import (LanguageAdminView, LanguageAPIView, PermissionsUsersJSON,
               ProjectAdminView, ProjectAPIView, UserAdminView, UserAPIView,
               adminroot, dashboard)


urlpatterns = [
    url(r'^$',
        dashboard.view,
        name='pootle-admin'),

    # FIXME: remove ad-hoc inclusion, make this pluggable
    url(r'^pages/',
        include(staticpages.urls.admin_patterns)),

    url(r'^users/$',
        UserAdminView.as_view(),
        name='pootle-admin-users'),
    url(r'^users/(?P<id>[0-9]+)/?$',
        UserAdminView.as_view(),
        name='pootle-admin-user-edit'),

    url(r'^languages/$',
        LanguageAdminView.as_view(),
        name='pootle-admin-languages'),
    url(r'^languages/(?P<id>[0-9]+)/?$',
        LanguageAdminView.as_view(),
        name='pootle-admin-language-edit'),

    url(r'^projects/$',
        ProjectAdminView.as_view(),
        name='pootle-admin-projects'),
    url(r'^projects/(?P<id>[0-9]+)/?$',
        ProjectAdminView.as_view(),
        name='pootle-admin-project-edit'),

    url(r'^permissions/$',
        adminroot.view,
        name='pootle-admin-permissions'),

    url(r'^xhr/permissions/users/(?P<directory>[^/]*)/$',
        PermissionsUsersJSON.as_view(),
        name='pootle-permissions-users')]


api_patterns = [
    url(r'^users/?$',
        UserAPIView.as_view(),
        name='pootle-xhr-admin-users'),
    url(r'^users/(?P<id>[0-9]+)/?$',
        UserAPIView.as_view(),
        name='pootle-xhr-admin-user'),

    url(r'^languages/?$',
        LanguageAPIView.as_view(),
        name='pootle-xhr-admin-languages'),
    url(r'^languages/(?P<id>[0-9]+)/?$',
        LanguageAPIView.as_view(),
        name='pootle-xhr-admin-languages'),

    url(r'^projects/?$',
        ProjectAPIView.as_view(),
        name='pootle-xhr-admin-projects'),
    url(r'^projects/(?P<id>[0-9]+)/?$',
        ProjectAPIView.as_view(),
        name='pootle-xhr-admin-project'),
]

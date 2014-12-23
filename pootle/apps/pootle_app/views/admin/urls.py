#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2014 Zuza Software Foundation
# Copyright 2013-2015 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import include, patterns, url

import staticpages.urls

from . import (LanguageAdminView, LanguageAPIView, ProjectAdminView,
               ProjectAPIView, UserAdminView, UserAPIView)


urlpatterns = patterns('pootle_app.views.admin',
    url(r'^/?$',
        'dashboard.view',
        name='pootle-admin'),

    url(r'^/pages/',
        include(staticpages.urls.admin_patterns)),

    url(r'^/users/$',
        UserAdminView.as_view(),
        name='pootle-admin-users'),
    url(r'^/users/(?P<id>[0-9]+)/?$',
        UserAdminView.as_view(),
        name='pootle-admin-user-edit'),

    url(r'^/languages/$',
        LanguageAdminView.as_view(),
        name='pootle-admin-languages'),
    url(r'^/languages/(?P<id>[0-9]+)/?$',
        LanguageAdminView.as_view(),
        name='pootle-admin-language-edit'),

    url(r'^/projects/$',
        ProjectAdminView.as_view(),
        name='pootle-admin-projects'),
    url(r'^/projects/(?P<id>[0-9]+)/?$',
        ProjectAdminView.as_view(),
        name='pootle-admin-project-edit'),

    url(r'^/permissions/$',
        'adminroot.view',
        name='pootle-admin-permissions'),

    # XHR
    url(r'^/more-stats/?$',
        'dashboard.server_stats_more',
        name='pootle-admin-more-stats'),
)


api_patterns = patterns('',
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
)

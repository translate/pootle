#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import include, patterns, url

from .views import UserAPIView, UserDetailView, UserSettingsView


account_patterns = patterns('pootle_profile.views',
    url(r'^settings/$',
        UserSettingsView.as_view(),
        name='pootle-profile-edit'),
)


auth_patterns = patterns('django.contrib.auth.views',
    url(r'^password/change/$',
        'password_change',
        name='pootle-password-change'),
    url(r'^password/change/done/$',
        'password_change_done',
        name='password_change_done'),
    url(r'^password/reset/$',
        'password_reset',
        name='pootle-password-reset'),
    url(r'^password/reset/confirm/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>.+)/$',
        'password_reset_confirm',
        name='pootle-password-reset-confirm'),
    url(r'^password/reset/complete/$',
        'password_reset_complete',
        name='password_reset_complete'),
    url(r'^password/reset/done/$',
        'password_reset_done',
        name='password_reset_done'),
)


profile_patterns = patterns('pootle_profile.views',
    url(r'^(?P<username>[^/]+)/$',
        UserDetailView.as_view(),
        name='pootle-user-profile'),
    url(r'^(?P<username>[^/]+)/edit/?$',
        UserDetailView.as_view(),
        name='pootle-user-profile-edit'),
)


api_patterns = patterns('',
    url(r'^users/(?P<id>[0-9]+)/?$',
        UserAPIView.as_view(),
        name='pootle-xhr-user'),
)


urlpatterns = patterns('',
    url(r'^accounts/', include(account_patterns)),
    url(r'^accounts/', include(auth_patterns)),
    url(r'^user/', include(profile_patterns)),
    url(r'^xhr/', include(api_patterns)),
)

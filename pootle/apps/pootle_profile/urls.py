#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

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

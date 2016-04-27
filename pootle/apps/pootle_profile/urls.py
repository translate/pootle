# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import include, url

from .views import UserAPIView, UserDetailView, UserSettingsView


user_patterns = [
    url(r'^(?P<username>[^/]+)/$',
        UserDetailView.as_view(),
        name='pootle-user-profile'),
    url(r'^(?P<username>[^/]+)/edit/?$',
        UserDetailView.as_view(),
        name='pootle-user-profile-edit'),
    url(r'^(?P<username>[^/]+)/settings/$',
        UserSettingsView.as_view(),
        name='pootle-user-settings'),
]


api_patterns = [
    url(r'^users/(?P<id>[0-9]+)/?$',
        UserAPIView.as_view(),
        name='pootle-xhr-user'),
]


urlpatterns = [
    url(r'^user/', include(user_patterns)),
    url(r'^xhr/', include(api_patterns)),
]

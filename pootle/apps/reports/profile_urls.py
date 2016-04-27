# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from .views import (AddUserPaidTaskView, UserActivityView,
                    UserDetailedStatsView, UserStatsView)


urlpatterns = [
    url('^user/(?P<username>[^/]+)/stats/detailed/?$',
        UserDetailedStatsView.as_view(),
        name='pootle-user-detailed-stats'),
    url('^user/(?P<username>[^/]+)/stats/activity/?$',
        UserActivityView.as_view(),
        name='pootle-user-activity'),
    url('^user/(?P<username>[^/]+)/stats/$',
        UserStatsView.as_view(),
        name='pootle-user-stats'),
    url('^user/(?P<username>[^/]+)/paid-tasks/?$',
        AddUserPaidTaskView.as_view(),
        name='pootle-user-add-paid-task'),
]

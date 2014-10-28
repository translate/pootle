#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import patterns, url

from .views import (UserStatsView, UserDetailedStatsView,
                    UserActivityView, AddUserPaidTaskView)


urlpatterns = patterns('evernote_reports.views',
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
)

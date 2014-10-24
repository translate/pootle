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

from .views import (UserReportView, UserDetailedReportView,
                    UserActivityView, PaidTaskFormView)


urlpatterns = patterns('evernote_reports.views',
    url('^user/(?P<username>[^/]+)/stats/detailed/?$',
        UserDetailedReportView.as_view(),
        name='pootle-user-detailed-report'),
    url('^user/(?P<username>[^/]+)/stats/activity/?$',
        UserActivityView.as_view(),
        name='pootle-user-activity'),
    url('^user/(?P<username>[^/]+)/stats/$',
        UserReportView.as_view(),
        name='pootle-user-report'),
    url('^user/(?P<username>[^/]+)/paid-tasks/?$',
        PaidTaskFormView.as_view(),
        name='pootle-user-add-paid-task'),
)

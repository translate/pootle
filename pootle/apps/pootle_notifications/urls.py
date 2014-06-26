#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2014 Zuza Software Foundation
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

from pootle_notifications.feeds import NoticeFeed


urlpatterns = patterns('pootle_notifications',
    # Feed
    url(r'^(?P<path>.*)notices/rss.xml$',
        NoticeFeed(),
        name='pootle-notifications-feed'),

    url(r'^projects/(?P<project_code>[^/]*)/notices/$',
        'views.view',
        name='pootle-notifications-project-notices'),
    url(r'^(?P<language_code>[^/]*)/notices/$',
        'views.view',
        name='pootle-notifications-language-notices'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/notices/$',
        'views.view',
        name='pootle-notifications-tp-notices'),

    url(r'^(?P<path>.*)notices/(?P<notice_id>[0-9]+)/$',
        'views.view_notice_item',
        name='pootle-notifications-notice'),
)

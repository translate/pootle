#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009,2012 Zuza Software Foundation
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

from pootle_notifications import feeds
from pootle_notifications.views import NoticeFormPreview


urlpatterns = patterns('pootle_notifications',
    # Feed
    url(r'^(?P<path>.*)notices/rss.xml$',
        feeds.NoticeFeed(),
        name="pootle_notifications__feed"),
    url(r'^(?P<path>.*)notices/?$',
        NoticeFormPreview(),
        name="pootle_notifications__index"),
    (r'^(?P<path>.*)notices/(?P<notice_id>[0-9]+)/?$',
        'views.view_notice_item'),
)

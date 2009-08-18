#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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

from feeds import NoticeFeeds
from django.conf.urls.defaults import *
from pootle_notifications.views import *

urlpatterns = patterns('',
    (r'^notice/viewitem/(?P<notice_id>[^/]*)/$', view_notice_item),
    (r'^(?P<url>.*)/rss.xml/$', NoticeFeeds),
    (r'^(?P<language_code>[^/]*)/notices/$', lang_notices),
    (r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/notices/$', transproj_notices),
)

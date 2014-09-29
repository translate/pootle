#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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


urlpatterns = patterns('pootle_terminology.views',
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)'
        r'/terminology/extract/$',
        'extract',
        name='pootle-terminology-extract'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/terminology/',
        'manage',
        name='pootle-terminology-manage'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/(?P<path>.*?)'
        r'/terminology/',
        'manage',
        name='pootle-terminology-manage-store'),
)

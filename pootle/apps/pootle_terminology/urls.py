#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009, 2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import patterns, url


urlpatterns = patterns('pootle_terminology.views',
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'terminology_extract.html',
        'extract'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'terminology_manage.html',
        'manage'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'(?P<path>.*?)/terminology_manage.html',
        'manage'),
)

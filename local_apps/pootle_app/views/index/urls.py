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

from django.conf.urls.defaults import *

urlpatterns = patterns('pootle_app.views.index',
    (r'^login.html$',      'login.view'),
    (r'^logout.html$',     'logout.view'),
    (r'^robots.txt$',      'robots.view'),
    (r'^about.html$',      'about.view'),
#    (r'^register.html$',   'register.view'),
    (r'^activate.html$',   'activate.view'),
    (r'^(/|index.html)?$', 'index.view'),
)

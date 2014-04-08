#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.conf.urls import include, patterns, url

import staticpages.urls

urlpatterns = patterns('pootle_app.views.admin',
    url(r'^/?$',
        'dashboard.view',
        name='pootle-admin'),

    url(r'^/pages/',
        include(staticpages.urls.admin_patterns)),

    url(r'^/users/$',
        'adminusers.view',
        name='pootle-admin-users'),
    url(r'^/languages/$',
        'adminlanguages.view',
        name='pootle-admin-languages'),
    url(r'^/projects/$',
        'adminprojects.view',
        name='pootle-admin-projects'),
    url(r'^/permissions/$',
        'adminroot.view',
        name='pootle-admin-permissions'),

    # XHR
    url(r'^/more-stats/?$',
        'dashboard.server_stats_more',
        name='pootle-admin-more-stats'),
)

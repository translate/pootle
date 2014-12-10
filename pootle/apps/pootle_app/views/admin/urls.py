#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2014 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
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
    url(r'^/more-stats/$',
        'dashboard.server_stats_more',
        name='pootle-admin-more-stats'),
)

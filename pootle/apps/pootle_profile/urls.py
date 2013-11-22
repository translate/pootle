#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.conf.urls import include, patterns, url


urlpatterns = patterns('pootle_profile.views',
    url(r'^login/?$',
        'login'),
    url(r'^logout/?$',
        'logout'),
    url(r'^edit/?$',
        'profile_edit'),
    url(r'^personal/edit/?$',
        'edit_personal_info'),
)

urlpatterns += patterns('django.contrib.auth.views',
    url(r'^password/change/$',
        'password_change'),
    url(r'^password/change/done/$',
        'password_change_done'),
    url(r'^password/reset/$',
        'password_reset'),
    url(r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$',
        'password_reset_confirm'),
    url(r'^password/reset/complete/$',
        'password_reset_complete'),
    url(r'^password/reset/done/$',
        'password_reset_done'),
)

# Only include registration urls if registration is enabled.
if settings.CAN_REGISTER:
    urlpatterns += patterns('',
        url(r'^register/?$',
            'pootle_profile.views.register'),
        url(r'',
            include('registration.urls')),
    )

urlpatterns += patterns('',
    url(r'',
        include('profiles.urls')),
)

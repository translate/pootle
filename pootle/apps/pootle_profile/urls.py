#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
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

from django.conf import settings
from django.conf.urls import include, patterns


urlpatterns = patterns('pootle_profile.views',
    (r'^logout/?$',   'logout'),
    (r'^edit/?$', 'profile_edit'),
    (r'^personal/edit/?$',   'edit_personal_info'),
)

# Only include password-related urls if using password authentication
if settings.AUTHENTICATION == 'password':
    urlpatterns += patterns('pootle_profile.views',
        (r'^login/?$',    'login'),
    )
    urlpatterns += patterns('django.contrib.auth.views',
        (r'^password/change/$', 'password_change'),
        (r'^password/change/done/$', 'password_change_done'),
        (r'^password/reset/$', 'password_reset'),
        (r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'password_reset_confirm'),
        (r'^password/reset/complete/$', 'password_reset_complete'),
        (r'^password/reset/done/$', 'password_reset_done'),
    )

# Include OpenID urls if using openid authentication
if settings.AUTHENTICATION == 'openid':
    urlpatterns += patterns('',
        (r'', include('django_openid_auth.urls')),
    )

# Only include registration urls if registration is enabled
if settings.CAN_REGISTER:
    urlpatterns += patterns('',
        (r'^register/?$', 'pootle_profile.views.register'),
        (r'', include('registration.urls')),
    )

urlpatterns += patterns('',
    (r'', include('profiles.urls')),
)

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

from django.conf.urls.defaults import *
from django.conf import settings

urlpatterns = patterns('pootle_profile.views',
    (r'^login/?$',    'login'),
    (r'^logout/?$',   'logout'),
    (r'^personal/edit/?$',   'edit_personal_info'),
    (r'^password/change/$', 'django.contrib.auth.views.password_change'),
    (r'^password/change/done/$', 'django.contrib.auth.views.password_change_done'),
    (r'^password/reset/$', 'django.contrib.auth.views.password_reset'),
    (r'^password/reset/confirm/(?P<uidb36>[0-9A-Za-z]+)-(?P<token>.+)/$', 'django.contrib.auth.views.password_reset_confirm'),
    (r'^password/reset/complete/$', 'django.contrib.auth.views.password_reset_complete'),
    (r'^password/reset/done/$', 'django.contrib.auth.views.password_reset_done'),
)

# Onle include registration urls if registration is enabled
if settings.CAN_REGISTER:
    urlpatterns += patterns('', (r'', include('registration.urls')))

urlpatterns += patterns('',
    (r'',           include('profiles.urls')),
)

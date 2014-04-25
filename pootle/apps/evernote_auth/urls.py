#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Evernote Corporation
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

from django.conf.urls import patterns


urlpatterns = patterns('evernote_auth.views',
    (r'^accounts/evernote/login/link/?$','evernote_login_link', {},
        'evernote_login_link'),

    (r'^accounts/evernote/login/?$', 'evernote_login', {}, 'evernote_login'),
    (r'^accounts/evernote/create/login/?$', 'evernote_login',
        {'create': '/create'}, 'evernote_create_login'),

    (r'^accounts/evernote/return/?$', 'sso_return_view', {},
        'evernote_return'),
    (r'^accounts/evernote/return/(?P<redirect_to>.*)/?$',
        'sso_return_view', {}, 'evernote_return'),

    (r'^accounts/evernote/create/return/?$', 'sso_return_view',
        {'create': 1}, 'evernote_create_return'),
    (r'^accounts/evernote/create/return/(?P<redirect_to>.*)/?$',
        'sso_return_view', {'create': 1}, 'evernote_create_return'),

    (r'^accounts/evernote/link/?$', 'evernote_account_info', {},
        'evernote_account_link'),
    (r'^accounts/evernote/link/disconnect/?$', 'evernote_account_disconnect',
        {}, 'evernote_account_disconnect'),
)

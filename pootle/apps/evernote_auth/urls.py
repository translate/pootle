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

from django.conf.urls import patterns, url


urlpatterns = patterns('evernote_auth.views',
    url(r'^login/link/?$',
        'link',
        name='evernote_login_link'),

    url(r'^login/?$',
        'evernote_login',
        name='evernote_login'),
    url(r'^create/login/?$',
        'evernote_login',
        kwargs={'create': '/create'},
        name='evernote_create_login'),

    url(r'^return/(?P<redirect_to>.*)?/?$',
        'sso_return_view',
        name='evernote_return'),

    url(r'^create/return/(?P<redirect_to>.*)?/?$',
        'sso_return_view',
        kwargs={'create': 1},
        name='evernote_create_return'),

    url(r'^link/?$',
        'account_info',
        name='evernote_account_link'),
    url(r'^link/disconnect/?$',
        'unlink',
        name='evernote_account_disconnect'),
)

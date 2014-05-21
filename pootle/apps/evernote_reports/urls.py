#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
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


urlpatterns = patterns('evernote_reports.views',
    url(r'^$',
        'evernote_reports',
        name='evernote-reports'),
    url(r'^activity/?$',
        'user_date_prj_activity',
        name='evernote-reports-activity'),
    url(r'^users/?$',
        'users',
        name='evernote-reports-users'),
     url(r'^update_user_rates/?$',
         'update_user_rates',
         name='evernote-update-user-rates'),
)

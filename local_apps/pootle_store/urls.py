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

urlpatterns = patterns('pootle_store.views',
    (r'^(?P<pootle_path>.*)/export/xlf/?$', 'export_as_xliff'),
    (r'^(?P<pootle_path>.*)/download/?$', 'download'),
    (r'^(?P<pootle_path>.*)/translate/?$', 'translate'),
    (r'^(?P<pootle_path>.*)/meta/?$', 'get_tp_metadata'),
    (r'^(?P<pootle_path>.*)/meta/(?P<uid>[0-9]+)/?$', 'get_tp_metadata'),
    (r'^(?P<pootle_path>.*)/view/?$', 'get_view_units'),
    (r'^(?P<pootle_path>.*)/view/limit/(?P<limit>[0-9]+)/?$', 'get_view_units'),
    (r'^(?P<pootle_path>.*)/edit/(?P<uid>[0-9]+)/?$', 'get_edit_unit'),
    (r'^(?P<pootle_path>.*)/process/(?P<uid>[0-9]+)/(?P<type>submission|suggestion)/?$', 'process_submit'),
    (r'^suggestion/reject/(?P<uid>[0-9]+)/(?P<suggid>[0-9]+)/?$', 'reject_suggestion'),
    (r'^suggestion/accept/(?P<uid>[0-9]+)/(?P<suggid>[0-9]+)/?$', 'accept_suggestion'),
    (r'^qualitycheck/reject/(?P<uid>[0-9]+)/(?P<checkid>[0-9]+)/?$', 'reject_qualitycheck'),
)

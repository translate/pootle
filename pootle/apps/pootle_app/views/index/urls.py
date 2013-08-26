#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
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
from django.views.generic import TemplateView


urlpatterns = patterns('pootle_app.views.index',
    url(r'^robots.txt$',
        'robots.view',
        name='pootle-robots'),

    url(r'^/?$',
        'index.view',
        name='pootle-home'),

    url(r'^about/$',
        # FIXME: move this into a view file
        TemplateView.as_view(template_name='about/about.html'),
        name='pootle-about'),
    url(r'^about/contributors/$',
        'contributors.view',
        name='pootle-about-contributors'),

    url(r'^translate/$',
        'translate.view',
        name='pootle-translate'),
)

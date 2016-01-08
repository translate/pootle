#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from .index import AboutView


urlpatterns = [
    url(r'^robots.txt$',
        'robots.view',
        name='pootle-robots',
        prefix='pootle_app.views.index'),

    url(r'^/?$',
        'index.view',
        name='pootle-home',
        prefix='pootle_app.views.index'),

    url(r'^about/$',
        AboutView.as_view(),
        name='pootle-about',
        prefix='pootle_app.views.index'),
]

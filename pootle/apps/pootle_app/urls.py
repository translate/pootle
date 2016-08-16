# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import include, url

from .views.admin import urls as admin_urls


urlpatterns = [
    url(r'^admin/',
        include(admin_urls)),
    url(r'^xhr/admin/',
        include(admin_urls.api_patterns)),
    url(r'',
        include('pootle_app.views.index.urls')),
]

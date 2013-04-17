#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
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

from django.conf.urls import include, patterns
from django.conf import settings

from django.contrib import admin
admin.autodiscover()

from tastypie.api import Api

from pootle_language.api import LanguageResource


API_VERSION = 'v1'
pootle_api = Api(api_name=API_VERSION)
pootle_api.register(LanguageResource())

urlpatterns = patterns(
    '',
    (r'^django_admin/', include(admin.site.urls)),

    # JavaScript i18n
    (r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
     {'packages': ('pootle', ), }, ),

    # XXX: Do we really want to let Django serve these files in production?
    # Direct download of translation files
    (r'^export/(?P<path>.*)$', 'django.views.static.serve',
     {'document_root': settings.PODIRECTORY}, ),

    # External apps
    (r'^contact/', include('contact_form_i18n.urls')),
    (r'^accounts/', include('pootle_profile.urls')),

    # Pootle API URLs
    (r'^api/', include(pootle_api.urls)),

    # Pootle URLs
    (r'^pages/', include('staticpages.urls')),
    (r'', include('pootle_app.urls')),
    (r'^projects/', include('pootle_project.urls')),
    (r'', include('pootle_notifications.urls')),
    (r'', include('pootle_terminology.urls')),
    (r'', include('pootle_store.urls')),
    (r'', include('pootle_translationproject.urls')),
    (r'', include('pootle_language.urls')),
)

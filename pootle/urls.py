#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
# Copyright 2013-2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.conf import settings
from django.conf.urls import include, patterns, url
from django.contrib import admin


admin.autodiscover()

urlpatterns = patterns('',
    url(r'^django_admin/', include(admin.site.urls)),

    # JavaScript i18n.
    url(r'^jsi18n/$',
        'django.views.i18n.javascript_catalog',
        {'packages': ('pootle', ), }, ),

    # XXX: Do we really want to let Django serve these files in production?
    # Direct download of translation files.
    #
    # This is also used to provide reverse for the URL.
    url(r'^export/(?P<path>.*)$',
        'django.views.static.serve',
        {'document_root': settings.PODIRECTORY},
        name='pootle-export'),

    # External apps.
    url(r'^contact/', include('pootle_contact.urls')),
    url(r'^accounts/', include('allauth.urls')),
    url(r'^profiles/', include('accounts.urls')),
)

if settings.POOTLE_ENABLE_API:
    from api_factory import api_factory

    urlpatterns += patterns('',
        # Pootle API URLs.
        url(r'^api/', include(api_factory().urls)),
    )

urlpatterns += patterns('',
    # Pootle URLs.
    url(r'^pages/', include('staticpages.urls')),
    url(r'', include('pootle_app.urls')),
    url(r'', include('pootle_notifications.urls')),
    url(r'^projects/', include('pootle_project.urls')),
    url(r'', include('pootle_terminology.urls')),
    url(r'', include('pootle_store.urls')),
    url(r'', include('pootle_language.urls')),
    url(r'', include('pootle_translationproject.urls')),
)

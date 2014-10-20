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

from django.conf.urls import include, patterns, url


urlpatterns = patterns('',
    # JavaScript i18n
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
        {'packages': ('pootle', ), }, ),

    # URLs added by Evernote
    url(r'^accounts/evernote/', include('evernote_auth.urls')),
    url(r'^admin/reports/', include('evernote_reports.urls')),
    url(r'', include('evernote_reports.profile_urls')),

    # External apps
    url(r'^contact/', include('evernote_contact.urls')),
    url(r'', include('pootle_profile.urls')),

    # Pootle URLs
    url(r'^pages/', include('staticpages.urls')),
    url(r'', include('pootle_app.urls')),
    url(r'^projects/', include('pootle_project.urls')),
    url(r'', include('pootle_terminology.urls')),
    url(r'', include('pootle_store.urls')),
    url(r'', include('pootle_language.urls')),
    url(r'', include('pootle_translationproject.urls')),
)


# TODO: handler400
handler403 = 'pootle.core.views.permission_denied'
handler404 = 'pootle.core.views.page_not_found'
handler500 = 'pootle.core.views.server_error'

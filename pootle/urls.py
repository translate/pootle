#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf import settings
from django.conf.urls import include, patterns, url


urlpatterns = patterns('',
    # JavaScript i18n
    url(r'^jsi18n/$', 'django.views.i18n.javascript_catalog',
        {'packages': ('pootle', ), }, ),

    # Allauth
    url(r'^accounts/', include('allauth.urls')),

    # URLs added by Evernote
    url(r'^admin/reports/', include('evernote_reports.urls')),
    url(r'', include('evernote_reports.profile_urls')),
)

# XXX should be autodiscovered
if "import_export" in settings.INSTALLED_APPS:
    urlpatterns += patterns('',
        # Pootle offline translation support URLs.
        url(r'', include('import_export.urls')),
    )

urlpatterns += patterns('',
    # External apps
    url(r'^contact/', include('contact.urls')),
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

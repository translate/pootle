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
from django.conf import settings
from os import path

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

DJANGO_MEDIA = path.join(path.dirname(admin.__file__), 'media')

urlpatterns = patterns('',
    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^static/(?P<path>.*)$',  'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^media/(?P<path>.*)$',   'django.views.static.serve', {'document_root': DJANGO_MEDIA}),
    (r'^django_admin/(.*)',      admin.site.root),
    (r'^login.html$',           'pootle_app.views.auth.login'),
    (r'^logout.html$',          'pootle_app.views.auth.logout'),
    (r'^admin',                 include('pootle_app.views.admin.urls')),
    (r'^home',                  include('pootle_app.views.home.urls')),
    (r'^projects',              include('pootle_app.views.projects.urls')),
    (r'',                       include('pootle_app.views.index.urls')),
    (r'',                       include('pootle_app.views.language.urls')),
)

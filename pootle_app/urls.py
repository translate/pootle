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

# CSS_DIR    = settings.MEDIA_ROOT
# IMAGES_DIR = path.join(settings.MEDIA_ROOT, 'images')
# JS_DIR     = path.join(settings.MEDIA_ROOT, 'js')
DJANGO_MEDIA = path.join(path.dirname(admin.__file__), 'media')

urlpatterns = patterns('',
    # Example:
    # (r'^pootle_app/', include('pootle_app.foo.urls')),

    # Uncomment the admin/doc line below and add 'django.contrib.admindocs' 
    # to INSTALLED_APPS to enable admin documentation:
    # (r'^admin/doc/', include('django.contrib.admindocs.urls')),

    # Uncomment the next line to enable the admin:
    (r'^static/(?P<path>.*)$',  'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^media/(?P<path>.*)$',  'django.views.static.serve', {'document_root': DJANGO_MEDIA}),
    #(r'^django_admin/(.*)', admin.site.root),
    #(r'^(?P<path>.*[.]css)$',  'django.views.static.serve', {'document_root': CSS_DIR}),
    #(r'^(?P<path>(:?images|js|doc)/.*)$', 'django.views.static.serve', {'document_root': settings.MEDIA_ROOT}),
    (r'^login.html$', 'pootle_app.views.auth.login'),
    (r'^logout.html$', 'pootle_app.views.auth.logout'),
    (r'^admin', include('pootle_app.views.admin.urls')),
    (r'^home',  include('pootle_app.views.home.urls')),
    (r'^projects', include('pootle_app.views.projects.urls')),
    (r'^robots.txt$', 'pootle_app.views.index.view.robots'),
    (r'^about.html$', 'pootle_app.views.index.view.about'),
    (r'^register.html$', 'pootle_app.views.index.view.register'),
    (r'^activate.html$', 'pootle_app.views.index.view.activate'),
    (r'^(/|index.html)?$', 'pootle_app.views.index.view.index'),
    (r'', include('pootle_app.views.language.urls')),
)


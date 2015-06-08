#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import patterns, url


urlpatterns = patterns('pootle_translationproject.views',
    # Admin views
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)'
        r'/admin/permissions/',
        'admin_permissions',
        name='pootle-tp-admin-permissions'),

    # Translation
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'translate/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'translate',
        name='pootle-tp-translate'),

    # Export view for proofreading
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'export-view/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'export_view',
        name='pootle-tp-export-view'),

    # Browser
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'browse',
        name='pootle-tp-browse'),
)

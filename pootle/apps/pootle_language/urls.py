#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import patterns, url


urlpatterns = patterns('pootle_language.views',
    url(r'^(?P<language_code>[^/]*)/$',
        'browse',
        name='pootle-language-browse'),

    url(r'^(?P<language_code>[^/]*)/translate/$',
        'translate',
        name='pootle-language-translate'),

    url(r'^(?P<language_code>[^/]*)/export-view/$',
        'export_view',
        name='pootle-language-export-view'),

    # Admin
    url(r'^(?P<language_code>[^/]*)/admin/permissions/$',
        'language_admin',
        name='pootle-language-admin-permissions'),
    url(r'^(?P<language_code>[^/]*)/admin/characters/$',
        'language_characters_admin',
        name='pootle-language-admin-characters'),
)

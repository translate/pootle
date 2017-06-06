# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from .views import (
    TPBrowseStoreView, TPBrowseView, TPPathsJSON, TPTranslateStoreView,
    TPTranslateView, admin_permissions)


urlpatterns = [
    # Admin views
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)'
        r'/admin/permissions/',
        admin_permissions,
        name='pootle-tp-admin-permissions'),

    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)'
        r'/paths/',
        TPPathsJSON.as_view(),
        name='pootle-tp-paths'),

    # Translation
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'translate/(?P<dir_path>(.*/)*)?$',
        TPTranslateView.as_view(),
        name='pootle-tp-translate'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'translate/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)$',
        TPTranslateStoreView.as_view(),
        name='pootle-tp-store-translate'),

    # Browser
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'(?P<dir_path>(.*/)*)?$',
        TPBrowseView.as_view(),
        name='pootle-tp-browse'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        TPBrowseStoreView.as_view(),
        name='pootle-tp-store-browse')
]

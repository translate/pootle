# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import include, url

from pootle_store.urls import unit_xhr_urlpatterns

from .views import VFolderTPTranslateView, get_vfolder_units


vfolder_urlpatterns = [
    # TP Translate
    url(r'(?P<language_code>[^/]*)/'
        r'(?P<project_code>[^/]*)/translate/(?P<dir_path>(.*/)*)?/?',
        VFolderTPTranslateView.as_view(),
        name='pootle-vfolder-tp-translate'),
    url(r'xhr/units/$',
        get_vfolder_units,
        name='vfolder-pootle-xhr-units')]


urlpatterns = [
    url("^\+\+vfolder/(?P<vfolder_name>[^/]*)/", include(vfolder_urlpatterns)),
    url("^\+\+vfolder/(?P<vfolder_name>[^/]*)/", include(unit_xhr_urlpatterns))]

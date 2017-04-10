# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from . import ProjectUserView, ProjectAPIView


urlpatterns = [
    url(r'^projects/$',
        ProjectUserView.as_view(),
        name='pootle-user-projects'),
    url(r'^projects/(?P<id>[0-9]*)/?$',
        ProjectUserView.as_view(),
        name='pootle-user-project-edit'),
]


api_patterns = [
    url(r'^projects/?$',
        ProjectAPIView.as_view(),
        name='pootle-xhr-user-projects'),
    url(r'^projects/(?P<id>[0-9]*)/?$',
        ProjectAPIView.as_view(),
        name='pootle-xhr-user-project'),
]

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from .views import ProjectFSAdminView


urlpatterns = [
    url(r'^admin/projects/(?P<project_code>[^/]*)/fs/?$',
        ProjectFSAdminView.as_view(),
        name='pootle-admin-project-fs')]

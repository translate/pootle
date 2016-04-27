# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from .views import (
    ProjectBrowseView, ProjectExportView, ProjectsBrowseView,
    ProjectsExportView, ProjectsTranslateView, ProjectTranslateView,
    ProjectAdminView, project_admin_permissions)


urlpatterns = [
    # All projects
    url(r'^$',
        ProjectsBrowseView.as_view(),
        name='pootle-projects-browse'),

    url(r'^translate/$',
        ProjectsTranslateView.as_view(),
        name='pootle-projects-translate'),

    url(r'^export-view/$',
        ProjectsExportView.as_view(),
        name='pootle-projects-export'),

    # Admin
    url(r'^(?P<project_code>[^/]*)/admin/languages/$',
        ProjectAdminView.as_view(),
        name='pootle-project-admin-languages'),
    url(r'^(?P<project_code>[^/]*)/admin/permissions/$',
        project_admin_permissions,
        name='pootle-project-admin-permissions'),

    # Specific project
    url(r'^(?P<project_code>[^/]*)/translate/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        ProjectTranslateView.as_view(),
        name='pootle-project-translate'),

    url(r'^(?P<project_code>[^/]*)/export-view/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        ProjectExportView.as_view(),
        name='pootle-project-export'),

    url(r'^(?P<project_code>[^/]*)/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        ProjectBrowseView.as_view(),
        name='pootle-project-browse')
]

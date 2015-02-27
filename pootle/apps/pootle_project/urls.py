#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

from django.conf.urls import patterns, url


urlpatterns = patterns('pootle_project.views',
    # All projects
    url(r'^$',
        'projects_overview',
        name='pootle-projects-overview'),

    url(r'^translate/$',
        'projects_translate',
        name='pootle-projects-translate'),

    url(r'^export-view/$',
        'projects_export_view',
        name='pootle-projects-export-view'),

    # Admin
    url(r'^(?P<project_code>[^/]*)/admin/languages/$',
        'project_admin',
        name='pootle-project-admin-languages'),
    url(r'^(?P<project_code>[^/]*)/admin/permissions/$',
        'project_admin_permissions',
        name='pootle-project-admin-permissions'),

    # Specific project
    url(r'^(?P<project_code>[^/]*)/translate/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'translate',
        name='pootle-project-translate'),

    url(r'^(?P<project_code>[^/]*)/export-view/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'export_view',
        name='pootle-project-export-view'),

    url(r'^(?P<project_code>[^/]*)/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'overview',
        name='pootle-project-overview'),
)

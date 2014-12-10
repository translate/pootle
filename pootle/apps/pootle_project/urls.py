#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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
    url(r'^(?P<project_code>[^/]*)/admin/settings/$',
        'project_settings_edit',
        name='pootle-project-admin-settings'),
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

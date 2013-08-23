#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

from django.conf.urls import patterns, url


urlpatterns = patterns('pootle_project.views',
    # Listing of all projects
    (r'^$',
        'projects_index'),

    # Specific project
    url(r'^(?P<project_code>[^/]*)/$',
        'project_language_index',
        name='project.overview'),

    # XHR views
    url(r'^(?P<project_code>[^/]*)/ajax-add-tag-to-tp/?$',
        'ajax_add_tag_to_tp_in_project',
        name='project.ajax_add_tag_to_tp'),
    url(r'^ajax-remove-tag-from-tp/(?P<tp_id>[^/]*)/(?P<tag_name>.*\.*)?$',
        'ajax_remove_tag_from_tp_in_project',
        name='project.ajax_remove_tag_from_tp'),
    (r'^(?P<project_code>[^/]*)/edit_settings.html?$',
        'project_settings_edit'),

    # Admin
    (r'^(?P<project_code>[^/]*)/admin.html$',
        'project_admin'),
    (r'^(?P<project_code>[^/]*)/permissions.html$',
        'project_admin_permissions'),
)

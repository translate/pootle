#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
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
    url(r'^$',
        'projects_index'),

    # Specific project
    url(r'^(?P<project_code>[^/]*)/$',
        'overview',
        name='pootle-project-overview'),

    url(r'^(?P<project_code>[^/]*)/translate/$',
        'translate',
        name='pootle-project-translate'),

    # XHR views
    url(r'^(?P<project_code>[^/]*)/ajax-add-tag-to-tp/?$',
        'ajax_add_tag_to_tp_in_project',
        name='project.ajax_add_tag_to_tp'),
    url(r'^(?P<project_code>[^/]*)/ajax-remove-tag-from-tp/'
        r'(?P<language_code>[^/]*)/(?P<tag_name>.*\.*)?$',
        'ajax_remove_tag_from_tp_in_project',
        name='project.ajax_remove_tag_from_tp'),
    url(r'^ajax/tags/list/(?P<project_code>.*\.*)?$',
        'ajax_list_tags',
        name='pootle-project-ajax-list-tags'),
    url(r'^(?P<project_code>[^/]*)/edit_settings.html?$',
        'project_settings_edit'),

    # Admin
    url(r'^(?P<project_code>[^/]*)/admin.html$',
        'project_admin',
        name='pootle-project-admin'),
    url(r'^(?P<project_code>[^/]*)/permissions.html$',
        'project_admin_permissions',
        name='pootle-project-permissions'),
)

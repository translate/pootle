#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2012 Zuza Software Foundation
# Copyright 2013 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.conf.urls import patterns, url


urlpatterns = patterns('pootle_translationproject.views',
    # Admin views
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)'
        r'/admin/permissions/',
        'admin_permissions',
        name='pootle-tp-admin-permissions'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)'
        r'/admin/settings/$',
        'edit_settings',
        name='pootle-tp-admin-settings'),

    # Management actions
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/rescan/?$',
        'rescan_files',
        name='pootle-tp-rescan'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/update/?$',
        'update_against_templates',
        name='pootle-tp-update-against-templates'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/delete/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'delete_path_obj',
        name='pootle-tp-delete-path-obj'),

    # VCS
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'vcs-commit/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'vcs_commit',
        name='pootle-vcs-commit'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'vcs-update/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'vcs_update',
        name='pootle-vcs-update'),

    # Exporting files
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'(?P<file_path>.*)export/zip/$',
        'export_zip',
        name='pootle-tp-export-zip'),

    # Translation
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'translate/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'translate',
        name='pootle-tp-translate'),

    # Export view for proofreading
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'export-view/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'export_view',
        name='pootle-tp-export-view'),

    # Overview
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'overview',
        name='pootle-tp-overview'),
)

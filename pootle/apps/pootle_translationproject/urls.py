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
    (r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/((.*/)*)admin_permissions.html$',
        'admin_permissions'),

    # Management actions
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/rescan/?$',
        'rescan_files',
        name='tp.rescan'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/update/?$',
        'update_against_templates',
        name='tp.update_against_templates'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/delete/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'delete_path_obj',
        name='tp.delete_path_obj'),

    # VCS
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'vcs-commit/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'vcs_commit',
        name='pootle-vcs-commit'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'vcs-update/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'vcs_update',
        name='pootle-vcs-update'),

    # XHR views
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'edit_settings.html$',
        'edit_settings',
        name='pootle-tp-ajax-edit-settings'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/summary/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'path_summary_more',
        name='tp.path_summary_more'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/ajax-add-tag/?$',
        'ajax_add_tag_to_tp',
        name='tp.ajax_add_tag'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/ajax-remove-tag/'
        r'(?P<tag_name>.*\.*)?$',
        'ajax_remove_tag_from_tp',
        name='tp.ajax_remove_tag'),

    # Exporting files
    (r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/(?P<file_path>.*)export/zip$',
        'export_zip'),

    # Translation
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'translate/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'translate',
        name='pootle-tp-translate'),

    # Export view for proofreading
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'export-view/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'export_view',
        name='export-view'),

    # Goals
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'(?P<dir_path>(.*/)*)goals$',
        'goals_overview',
        name='pootle-tp-goals'),
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'goals/(?P<goal_slug>[a-z0-9-]+)/real-path/'
        r'(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'overview',
        name='pootle-tp-goal-drill-down'),

    # Overview
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'overview',
        name='pootle-tp-overview'),
)

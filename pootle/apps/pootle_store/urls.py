#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008-2013 Zuza Software Foundation
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

urlpatterns = patterns('pootle_store.views',
    # Translation
    (r'^(?P<pootle_path>.*)/translate/?$',
        'translate'),

    # Export list view
    url(r'^(?P<language_code>[^/]*)/(?P<project_code>[^/]*)/'
        r'export-view/(?P<dir_path>(.*/)*)(?P<filename>.*\.*)?$',
        'export_view',
        name='export-view'),

    # Download and export
    (r'^download/(?P<pootle_path>.*)/?$',
        'download'),
    (r'^export-file/xlf/(?P<pootle_path>.*)/?$',
        'export_as_xliff'),
    (r'^export-file/(?P<filetype>.*)/(?P<pootle_path>.*)/?$',
        'export_as_type'),

    # XHR
    (r'^checks/(?P<pootle_path>.*)/?$',
        'get_failing_checks_store'),

    (r'^view/(?P<pootle_path>.*)/?$',
        'get_view_units_store'),
    (r'^view/(?P<limit>[0-9]+)/(?P<pootle_path>.*)/?$',
        'get_view_units_store'),

    (r'^unit/context/(?P<uid>[0-9]+)/?$',
        'get_more_context'),
    (r'^unit/edit/(?P<uid>[0-9]+)/?$',
        'get_edit_unit'),
    (r'^unit/submit/(?P<uid>[0-9]+)/?$',
        'submit'),
    (r'^unit/suggest/(?P<uid>[0-9]+)/?$',
        'suggest'),
    (r'^unit/timeline/(?P<uid>[0-9]+)/?$',
        'timeline'),
    (r'^unit/comment/(?P<uid>[0-9]+)/?$',
        'comment'),

    (r'^suggestion/reject/(?P<uid>[0-9]+)/(?P<suggid>[0-9]+)/?$',
        'reject_suggestion'),
    (r'^suggestion/accept/(?P<uid>[0-9]+)/(?P<suggid>[0-9]+)/?$',
        'accept_suggestion'),

    (r'^vote/clear/(?P<voteid>[0-9]+)/?$',
        'clear_vote'),
    (r'^vote/up/(?P<uid>[0-9]+)/(?P<suggid>[0-9]+)/?$',
        'vote_up'),

    (r'^qualitycheck/reject/(?P<uid>[0-9]+)/(?P<checkid>[0-9]+)/?$',
        'reject_qualitycheck'),

    # XHR for tags.
    url(r'^ajax/tags/add/store/(?P<store_pk>[0-9]+)?$',
        'ajax_add_tag_to_store',
        name='pootle-store-ajax-add-tag'),

    url(r'^ajax/tags/remove/(?P<tag_slug>[a-z0-9-]+)/store/'
        r'(?P<store_pk>[0-9]+)?$',
        'ajax_remove_tag_from_store',
        name='pootle-store-ajax-remove-tag'),
)

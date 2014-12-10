#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
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

urlpatterns = patterns('pootle_store.views',
    # Download and export
    url(r'^download/(?P<pootle_path>.*)/?$',
        'download',
        name='pootle-store-download'),
    url(r'^export-file/xlf/(?P<pootle_path>.*)/?$',
        'export_as_xliff',
        name='pootle-store-export-xliff'),

    # XHR
    url(r'^xhr/stats/checks/?$',
        'get_qualitycheck_stats',
        name='pootle-xhr-stats-checks'),
    url(r'^xhr/stats/overview/?$',
        'get_overview_stats',
        name='pootle-xhr-stats-overview'),

    url(r'^xhr/units/?$',
        'get_units',
        name='pootle-xhr-units'),

    url(r'^xhr/units/(?P<uid>[0-9]+)/?$',
        'submit',
        name='pootle-xhr-units-submit'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/comment/?$',
        'comment',
        name='pootle-xhr-units-comment'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/context/?$',
        'get_more_context',
        name='pootle-xhr-units-context'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/edit/?$',
        'get_edit_unit',
        name='pootle-xhr-units-edit'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/timeline/?$',
        'timeline',
        name='pootle-xhr-units-timeline'),

    url(r'^xhr/units/(?P<uid>[0-9]+)/suggestions/?$',
        'suggest',
        name='pootle-xhr-units-suggest'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/suggestions/(?P<suggid>[0-9]+)/accept/?$',
        'accept_suggestion',
        name='pootle-xhr-units-suggestion-accept'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/suggestions/(?P<suggid>[0-9]+)/reject/?$',
        'reject_suggestion',
        name='pootle-xhr-units-suggestion-reject'),

    url(r'^xhr/units/(?P<uid>[0-9]+)/checks/(?P<check_id>[0-9]+)/toggle/?$',
        'toggle_qualitycheck',
        name='pootle-xhr-units-checks-toggle'),
)

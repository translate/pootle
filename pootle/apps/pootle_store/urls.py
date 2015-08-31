#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import patterns, url

urlpatterns = patterns('pootle_store.views',
    # permalinks
    url(r'^unit/(?P<uid>[0-9]+)/?$',
        'permalink_redirect',
        name='pootle-unit-permalink'),

    # XHR
    url(r'^xhr/stats/checks/?$',
        'get_qualitycheck_stats',
        name='pootle-xhr-stats-checks'),
    url(r'^xhr/stats/?$',
        'get_stats',
        name='pootle-xhr-stats'),

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
    url(r'^xhr/units/(?P<uid>[0-9]+)/suggestions/(?P<sugg_id>[0-9]+)/?$',
        'manage_suggestion',
        name='pootle-xhr-units-suggest-manage'),

    url(r'^xhr/units/(?P<uid>[0-9]+)/checks/(?P<check_id>[0-9]+)/toggle/?$',
        'toggle_qualitycheck',
        name='pootle-xhr-units-checks-toggle'),
)

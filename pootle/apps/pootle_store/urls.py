#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url


urlpatterns = [
    # permalinks
    url(r'^unit/(?P<uid>[0-9]+)/?$',
        'permalink_redirect',
        name='pootle-unit-permalink',
        prefix='pootle_store.views'),

    # XHR
    url(r'^xhr/stats/checks/?$',
        'get_qualitycheck_stats',
        name='pootle-xhr-stats-checks',
        prefix='pootle_store.views'),
    url(r'^xhr/stats/?$',
        'get_stats',
        name='pootle-xhr-stats',
        prefix='pootle_store.views'),

    url(r'^xhr/units/?$',
        'get_units',
        name='pootle-xhr-units',
        prefix='pootle_store.views'),

    url(r'^xhr/units/(?P<uid>[0-9]+)/?$',
        'submit',
        name='pootle-xhr-units-submit',
        prefix='pootle_store.views'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/comment/?$',
        'comment',
        name='pootle-xhr-units-comment',
        prefix='pootle_store.views'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/context/?$',
        'get_more_context',
        name='pootle-xhr-units-context',
        prefix='pootle_store.views'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/edit/?$',
        'get_edit_unit',
        name='pootle-xhr-units-edit',
        prefix='pootle_store.views'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/timeline/?$',
        'timeline',
        name='pootle-xhr-units-timeline',
        prefix='pootle_store.views'),

    url(r'^xhr/units/(?P<uid>[0-9]+)/suggestions/?$',
        'suggest',
        name='pootle-xhr-units-suggest',
        prefix='pootle_store.views'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/suggestions/(?P<sugg_id>[0-9]+)/?$',
        'manage_suggestion',
        name='pootle-xhr-units-suggest-manage',
        prefix='pootle_store.views'),

    url(r'^xhr/units/(?P<uid>[0-9]+)/checks/(?P<check_id>[0-9]+)/toggle/?$',
        'toggle_qualitycheck',
        name='pootle-xhr-units-checks-toggle',
        prefix='pootle_store.views'),
]

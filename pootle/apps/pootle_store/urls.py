# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from . import views


get_units_urlpatterns = [
    url(r'^xhr/units/?$',
        views.get_units,
        name='pootle-xhr-units')]

unit_xhr_urlpatterns = [

    # XHR
    url(r'^xhr/units/(?P<uid>[0-9]+)/?$',
        views.UnitSubmitJSON.as_view(),
        name='pootle-xhr-units-submit'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/comment/?$',
        views.comment,
        name='pootle-xhr-units-comment'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/context/?$',
        views.get_more_context,
        name='pootle-xhr-units-context'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/edit/?$',
        views.UnitEditJSON.as_view(),
        name='pootle-xhr-units-edit'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/timeline/?$',
        views.UnitTimelineJSON.as_view(),
        name='pootle-xhr-units-timeline'),

    url(r'^xhr/units/(?P<uid>[0-9]+)/suggestions/?$',
        views.UnitAddSuggestionJSON.as_view(),
        name='pootle-xhr-units-suggest'),
    url(r'^xhr/units/(?P<uid>[0-9]+)/suggestions/(?P<sugg_id>[0-9]+)/?$',
        views.UnitSuggestionJSON.as_view(),
        name='pootle-xhr-units-suggest-manage'),

    url(r'^xhr/units/(?P<uid>[0-9]+)/checks/(?P<check_id>[0-9]+)/toggle/?$',
        views.toggle_qualitycheck,
        name='pootle-xhr-units-checks-toggle'),
]

urlpatterns = (
    [url(r'^unit/(?P<uid>[0-9]+)/?$',
         views.permalink_redirect,
         name='pootle-unit-permalink')]
    + get_units_urlpatterns
    + unit_xhr_urlpatterns)

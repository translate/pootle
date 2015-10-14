#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import include, patterns, url

from .views import (AdminTemplateView, PageCreateView, PageDeleteView,
                    PageUpdateView)


page_patterns = patterns('',
    url(r'^legal/agreement/$',
        'staticpages.views.legal_agreement',
        name='pootle-staticpages-legal-agreement'),
    url(r'^(?P<virtual_path>.+)/$',
        'staticpages.views.display_page',
        name='pootle-staticpages-display'),
)

admin_patterns = patterns('',
    url(r'^$',
        AdminTemplateView.as_view(),
        name='pootle-staticpages'),

    url(r'^(?P<page_type>[^/]+)/add/?$',
        PageCreateView.as_view(),
        name='pootle-staticpages-create'),
    url(r'^(?P<page_type>[^/]+)/(?P<pk>\d+)/?$',
        PageUpdateView.as_view(),
        name='pootle-staticpages-edit'),
    url(r'^(?P<page_type>[^/]+)/(?P<pk>\d+)/delete/?$',
        PageDeleteView.as_view(),
        name='pootle-staticpages-delete'),
)


xhr_patterns = patterns('',
    url(r'^preview/?$',
        'staticpages.views.preview_content',
        name='pootle-xhr-preview'),
)


urlpatterns = patterns('',
    url(r'^pages/',
        include(page_patterns)),
    url(r'^xhr/',
        include(xhr_patterns)),
)

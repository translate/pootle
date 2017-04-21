# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url
from django.views.generic import TemplateView

from .index import AboutView, IndexView


urlpatterns = [
    url(r'^robots\.txt$',
        TemplateView.as_view(template_name='robots.txt',
                             content_type='text/plain'),
        name="pootle-robots"),

    url(r'^$',
        IndexView.as_view(),
        name='pootle-home'),

    url(r'^about/$',
        AboutView.as_view(),
        name='pootle-about'),
]

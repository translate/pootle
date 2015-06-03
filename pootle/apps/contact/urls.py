#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import patterns, url

from .views import ContactFormView, ReportFormView


urlpatterns = patterns('',
    url(r'^$',
        ContactFormView.as_view(),
        name='pootle-contact'),
    url(r'report/$',
        ReportFormView.as_view(),
        name='pootle-contact-report-error'),
)

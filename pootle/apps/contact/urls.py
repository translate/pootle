#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

from django.conf.urls import patterns, url

from .views import PootleContactFormView, PootleReportFormView


urlpatterns = patterns('',
    url(r'^$',
        PootleContactFormView.as_view(),
        name='pootle-contact'),
    url(r'report/$',
        PootleReportFormView.as_view(),
        name='pootle-contact-report-error'),
)

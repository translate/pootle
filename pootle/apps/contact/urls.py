# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from .views import ContactFormTemplateView, ContactFormView, ReportFormView


urlpatterns = [
    url(r'^$',
        ContactFormTemplateView.as_view(),
        name='pootle-contact'),
    url(r'^xhr/$',
        ContactFormView.as_view(),
        name='pootle-contact-xhr'),
    url(r'report/$',
        ReportFormView.as_view(),
        name='pootle-contact-report-error'),
]

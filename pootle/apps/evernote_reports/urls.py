#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import patterns, url


urlpatterns = patterns('evernote_reports.views',
    url(r'^$',
        'evernote_reports',
        name='evernote-reports'),
    url(r'^detailed/?$',
        'evernote_reports_detailed',
        name='evernote-reports-detailed'),
    url(r'^activity/?$',
        'user_date_prj_activity',
        name='evernote-reports-activity'),
    url(r'^users/?$',
        'users',
        name='evernote-reports-users'),
    url(r'^rates/?$',
        'update_user_rates',
        name='evernote-update-user-rates'),
    url(r'^paid-tasks/?$',
        'add_paid_task',
        name='evernote-add-paid-task'),
    url(r'paid-tasks/(?P<task_id>[0-9]+)?$',
        'remove_paid_task',
        name='evernote-remove-paid-task'),
)

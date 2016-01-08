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
    url(r'^$',
        'reports',
        name='pootle-reports',
        prefix='reports.views'),
    url(r'^detailed/?$',
        'reports_detailed',
        name='pootle-reports-detailed',
        prefix='reports.views'),
    url(r'^activity/?$',
        'user_date_prj_activity',
        name='pootle-reports-activity',
        prefix='reports.views'),
    url(r'^users/?$',
        'users',
        name='pootle-reports-users',
        prefix='reports.views'),
    url(r'^rates/?$',
        'update_user_rates',
        name='pootle-reports-update-user-rates',
        prefix='reports.views'),
    url(r'^paid-tasks/?$',
        'add_paid_task',
        name='pootle-reports-add-paid-task',
        prefix='reports.views'),
    url(r'paid-tasks/(?P<task_id>[0-9]+)?$',
        'remove_paid_task',
        name='pootle-reports-remove-paid-task',
        prefix='reports.views'),
]

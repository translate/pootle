# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from django.conf.urls import url

from . import views


urlpatterns = [
    url(r'^$',
        views.reports,
        name='pootle-reports'),
    url(r'^detailed/?$',
        views.reports_detailed,
        name='pootle-reports-detailed'),
    url(r'^activity/?$',
        views.user_date_prj_activity,
        name='pootle-reports-activity'),
    url(r'^users/?$',
        views.users,
        name='pootle-reports-users'),
    url(r'^rates/?$',
        views.update_user_rates,
        name='pootle-reports-update-user-rates'),
    url(r'^paid-tasks/?$',
        views.add_paid_task,
        name='pootle-reports-add-paid-task'),
    url(r'paid-tasks/(?P<task_id>[0-9]+)?$',
        views.remove_paid_task,
        name='pootle-reports-remove-paid-task'),
]

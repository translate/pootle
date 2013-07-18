#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Evernote Corporation

from django.conf.urls.defaults import include, patterns

urlpatterns = patterns('evernote_reports.views',
    (r'^$', 'evernote_reports', {}, 'evernote_reports'),
    (r'^activity/?$', 'user_date_prj_activity', {}, 'user_date_prj_activity'),
    (r'^users/?$', 'users', {}, 'users_for_evernote_reports'),
)
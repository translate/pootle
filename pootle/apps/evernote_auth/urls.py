#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL2
# license. See the LICENSE file for a copy of the license and the AUTHORS file
# for copyright and authorship information.

from django.conf.urls import patterns, url


urlpatterns = patterns('evernote_auth.views',
    url(r'^$',
        'account_info',
        name='en-auth-account-info'),

    url(r'^link/?$',
        'link',
        name='en-auth-account-link'),
    url(r'^unlink/?$',
        'unlink',
        name='en-auth-account-unlink'),

    url(r'^login/?$',
        'sso_login',
        name='en-auth-sso-login'),
    url(r'^return/(?P<redirect_to>.*)/?$',
        'sso_callback',
        name='en-auth-sso-callback'),
)

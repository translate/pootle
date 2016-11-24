# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""
Custom Pootle authentication middleware that takes care of returning Pootle's
special `nobody` user instead of Django's own `AnonymousUser`.

The code has been slightly adapted from django.contrib.auth.middleware.

Note this customization would probably be unnecessary if there was a fix for
https://code.djangoproject.com/ticket/20313
"""

from django.contrib import auth
from django.utils.deprecation import MiddlewareMixin
from django.utils.functional import SimpleLazyObject


def get_user(request):
    if not hasattr(request, '_cached_user'):
        user = auth.get_user(request)
        request._cached_user = (user if user.is_authenticated else
                                auth.get_user_model().objects.get_nobody_user())
    return request._cached_user


class AuthenticationMiddleware(MiddlewareMixin):
    def process_request(self, request):
        assert hasattr(request, 'session'), (
            "The Django authentication middleware requires session middleware "
            "to be installed. Edit your MIDDLEWARE setting to insert "
            "'django.contrib.sessions.middleware.SessionMiddleware' before "
            "'django.contrib.auth.middleware.AuthenticationMiddleware'."
        )
        request.user = SimpleLazyObject(lambda: get_user(request))

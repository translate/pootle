#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013-2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import base64
import itertools
import re
import time

from pyDes import triple_des, ECB

from django.conf import settings
from django.contrib.auth import get_user_model

from ..models import EvernoteAccount


class AlreadyLinked(Exception):
    pass


class CookieExpired(Exception):
    pass


class CookieMissing(Exception):
    pass


class EvernoteBackend(object):
    """This is a Django authentication module which implements internal
    Evernote API for Evernote translation server.

    To use this module, simply add it to the tuple AUTHENTICATION_BACKENDS
    in settings.py.
    """
    AlreadyLinked = AlreadyLinked

    CookieExpired = CookieExpired

    CookieMissing = CookieMissing

    def authenticate(self, request=None, create_account=True):
        """Authenticate user using Evernote account credentials.

        :param request: the HttpRequest containing the authentication
                        details.
        :param create_account: create a new `EvernoteAccount` if it is
                               not found.
        """
        if request is None:
            return None

        data = self.get_cookie(request)

        try:
            account = EvernoteAccount.objects.get(evernote_id=data['id'])

            # It's not possible to link this account with another `user_id`
            if (request.user.is_authenticated() and
                request.user.id != account.user.id):
                raise AlreadyLinked
        except EvernoteAccount.DoesNotExist:
            if not create_account:
                return None

            account = EvernoteAccount(
                evernote_id=data['id'],
                email=data['email'],
                name=data['name'],
            )
            account.user = (request.user if request.user.is_authenticated()
                            else self.create_user(account))
            account.save()

        return account.user

    def get_cookie(self, request):
        cookie = request.COOKIES.get(settings.EN_SSO_COOKIE, None)

        if cookie is not None:
            data = base64.b64decode(cookie)

            des3 = triple_des(settings.EN_SSO_SECRET_KEY, ECB)
            match = re.match(r'i=(?P<id>[0-9]+),'
                             r'u=(?P<name>[^,]+),'
                             r'e=(?P<email>[^,]+),'
                             r'x=(?P<expired>[0-9]+)',
                             des3.decrypt(data))

            if match:
                data = match.groupdict()
                if time.time() > data['expired']:
                    raise CookieExpired

                return data

        raise CookieMissing

    def create_user(self, account):
        """Creates a new Pootle user and returns it.

        This tries to preserve as much information as possible from the
        given Evernote `account`.

        If the account's username is already taken by some other Pootle
        user, it'll auto-generate a username.
        """
        User = get_user_model()

        if not User.objects.filter(username=account.name).exists():
            username = account.name
        else:
            username = "%s@evernote" % account.name
            count = itertools.count(1)
            while User.objects.filter(username=username).exists():
                username = "%s@evernote_%s" % (account.name, count.next())

        user = User(username=username, email=account.email)
        user.set_password(User.objects.make_random_password())
        user.save()

        account.user_autocreated = True
        account.user = user
        account.save()

        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

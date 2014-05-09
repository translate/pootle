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

import itertools

from django.contrib.auth import get_user_model


class EvernoteBackend(object):
    """This is a Django authentication module which implements internal
    Evernote API for Evernote translation server.

    To use this module, simply add it to the tuple AUTHENTICATION_BACKENDS
    in settings.py.
    """

    def authenticate(self, account=None):
        """Authenticate user using Evernote account credentials."""
        if account is None:
            return None

        if account.user_id is None:
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
        else:
            user = account.user

        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

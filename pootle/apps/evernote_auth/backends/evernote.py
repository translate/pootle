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

    def authenticate(self, *args, **kwargs):
        """Authenticate user using social credentials.

        Authentication is made if this is the correct backend, backend
        verification is made by kwargs inspection for current backend
        name presence.
        """
        # Validate backend and arguments. Require that the Social Auth
        # response be passed in as a keyword argument, to make sure we
        # don't match the username/password calling conventions of
        # authenticate.
        if 'evernote_account' not in kwargs:
            return None

        User = get_user_model()
        ea = kwargs.get('evernote_account')

        if ea.user_id is None:
            if User.objects.filter(username=ea.name).count() == 0:
                username = ea.name
            else:
                username = "%s@evernote" % ea.name
                count = itertools.count(1)
                while User.objects.filter(username=username).count() > 0:
                    username = "%s@evernote_%s" % (ea.name, count.next())

            user = User(username=username, email=ea.email)
            user.set_password(User.objects.make_random_password())
            user.save()
            ea.user_autocreated=True
            ea.user = user
        else:
            user = ea.user

        return user

    def get_user(self, user_id):
        User = get_user_model()
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None

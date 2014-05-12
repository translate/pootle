#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
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

import pytest

from django.contrib import auth
from django.contrib.auth.models import AnonymousUser

from evernote_auth.backends.evernote import EvernoteBackend

from ...factories import EvernoteAccountFactory


AUTH_COOKIE = {
    'expired': '1400051841',
    'email': 'hi@example.com',
    'name': 'admin',
    'id': '01234567',
}


@pytest.mark.django_db
def test_auth_no_en_account(rf, monkeypatch, admin):
    """Tests authentication when an EvernoteAccount doesn't exist."""
    monkeypatch.setattr(EvernoteBackend, 'get_cookie',
                        lambda x, y: AUTH_COOKIE)
    request = rf.get('/')

    # First let's try with an authenticated user
    request.user = admin

    # Account doesn't exist and we don't want to create it
    assert auth.authenticate(request=request, create_account=False) == None

    # New account will be created
    user = auth.authenticate(request=request)
    assert user == admin
    assert user.evernote_account.evernote_id == AUTH_COOKIE['id']

    # Now anonymous users
    request.user = AnonymousUser()

    # User doesn't exist, a new one will be created using the cookie data
    user = auth.authenticate(request=request)
    assert user.username == AUTH_COOKIE['name']

    # If the username is already taken, it'll auto-generate a new one
    AUTH_COOKIE['id'] = '76543210'
    user = auth.authenticate(request=request)
    assert user.username == '{0}@evernote'.format(AUTH_COOKIE['name'])

    # And yet another one
    AUTH_COOKIE['id'] = '87654321'
    user = auth.authenticate(request=request)
    assert user.username == '{0}@evernote_1'.format(AUTH_COOKIE['name'])


def test_auth_has_en_account(rf, monkeypatch, admin, system):
    """Tests authentication when an EvernoteAccount already exists."""
    monkeypatch.setattr(EvernoteBackend, 'get_cookie',
                        lambda x, y: AUTH_COOKIE)
    request = rf.get('/')

    # This EvernoteAccount is linked with the `admin` user
    request.user = admin
    account = EvernoteAccountFactory.create(
            evernote_id=AUTH_COOKIE['id'],
            user=admin,
    )

    # Account is there, must return our user
    user = auth.authenticate(request=request, create_account=False)
    assert user == request.user

    # Account already linked with another user
    with pytest.raises(EvernoteBackend.AlreadyLinked):
        request.user = system
        auth.authenticate(request=request)

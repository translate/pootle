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


def _require_user(username, fullname, password=None,
                  is_superuser=False):
    """Helper to get/create a new user."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    criteria = {
        'username': username,
        'first_name': fullname,
        'is_active': True,
        'is_superuser': is_superuser,
    }
    user, created = User.objects.get_or_create(**criteria)
    if created:
        if password is None:
            user.set_unusable_password()
        else:
            user.set_password(password)
        user.save()

    return user


@pytest.fixture
def nobody(db):
    """Require the default anonymous user."""
    return _require_user('nobody', 'any anonymous user')


@pytest.fixture
def default(db):
    """Require the default authenticated user."""
    return _require_user('default', 'any authenticated user',
                         password='')


@pytest.fixture
def system(db):
    """Require the system user."""
    return _require_user('system', 'system user')


@pytest.fixture
def admin(db):
    """Require the admin user."""
    return _require_user('admin', 'Administrator', password='admin',
                         is_superuser=True)

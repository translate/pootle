#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


def _require_user(username, fullname, password=None,
                  is_superuser=False, email=None):
    """Helper to get/create a new user."""
    from django.contrib.auth import get_user_model
    User = get_user_model()

    criteria = {
        'username': username,
        'full_name': fullname,
        'is_active': True,
        'is_superuser': is_superuser,
    }
    user, created = User.objects.get_or_create(**criteria)
    if created:
        if password is None:
            user.set_unusable_password()
        else:
            user.set_password(password)
        if email:
            user.email = email
        user.save()

    return user


@pytest.fixture
def trans_nobody():
    """Require the default anonymous user for use in a transactional test."""
    return _require_user('nobody', 'any anonymous user')


@pytest.fixture
def admin():
    """Require the admin user."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.get(username="admin")


@pytest.fixture
def member():
    """Require a member user."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.get(username="member")


@pytest.fixture
def trans_system():
    """Require the system user."""
    return _require_user('trans_system', 'Transactional system user')


@pytest.fixture
def trans_member():
    """Require a member user."""
    return _require_user('trans_member', 'Transactional member')


@pytest.fixture
def member_with_email():
    """Require a member user."""
    user = _require_user('member_with_email', 'Member with email')
    user.email = "member_with_email@this.test"
    user.save()
    return user


@pytest.fixture
def member2():
    """Require a member2 user."""
    from django.contrib.auth import get_user_model

    User = get_user_model()
    return User.objects.get(username="member2")


@pytest.fixture
def member2_with_email():
    """Require a member2 user."""
    user = _require_user('member2_with_email', 'Member2 with email')
    user.email = "member2_with_email@this.test"
    user.save()
    return user


@pytest.fixture
def evil_member():
    """Require a evil_member user."""
    return _require_user('evil_member', 'Evil member')


@pytest.fixture
def no_perms_user():
    """Require a user with no permissions."""
    return _require_user('no_perms_member', 'User with no permissions')

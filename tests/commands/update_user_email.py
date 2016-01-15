# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_user_email_nouser():
    with pytest.raises(CommandError) as e:
        call_command('update_user_email')
    assert "too few arguments" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_user_email_noemail_supplied(member):
    with pytest.raises(CommandError) as e:
        call_command('update_user_email', 'member')
    assert "too few arguments" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_user_email_unkonwnuser():
    with pytest.raises(CommandError) as e:
        call_command('update_user_email', 'not_a_user', 'email@address')
    assert "User not_a_user does not exist" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_user_email_new_email(capfd, member):
    call_command('update_user_email', 'member', 'new_email@address.com')
    out, err = capfd.readouterr()
    assert "Email updated: member, new_email@address.com" in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_user_email_bad_email(member):
    with pytest.raises(CommandError) as e:
        call_command('update_user_email', 'member', 'new_email@address')
    assert "Enter a valid email address." in str(e)

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
def test_verify_user_nouser(capfd):
    with pytest.raises(CommandError) as e:
        call_command('verify_user')
    assert "Either provide a 'user' to verify or use '--all'" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_verify_user_user_and_all(capfd):
    with pytest.raises(CommandError) as e:
        call_command('verify_user', '--all', 'member_with_email')
    assert "Either provide a 'user' to verify or use '--all'" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_verify_user_unknownuser(capfd):
    with pytest.raises(CommandError) as e:
        call_command('verify_user', 'not_a_user')
    assert "User not_a_user does not exist" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_verify_user_noemail(capfd, member):
    call_command('verify_user', 'member')
    out, err = capfd.readouterr()
    assert "You cannot verify an account with no email set" in err


@pytest.mark.cmd
@pytest.mark.django_db
def test_verify_user_hasemail(capfd, member_with_email):
    call_command('verify_user', 'member_with_email')
    out, err = capfd.readouterr()
    assert "User 'member_with_email' has been verified" in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_verify_user_all(capfd, member_with_email, member2_with_email):
    call_command('verify_user', '--all')
    out, err = capfd.readouterr()
    assert "Verified user 'member_with_email'" in out
    assert "Verified user 'member2_with_email'" in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_verify_user_multiple(capfd, member_with_email, member2_with_email):
    call_command('verify_user', 'member_with_email', 'member2_with_email')
    out, err = capfd.readouterr()
    assert "User 'member_with_email' has been verified" in out
    assert "User 'member2_with_email' has been verified" in out

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
def test_merge_user_nousers():
    with pytest.raises(CommandError) as e:
        call_command('merge_user')
    assert "too few arguments" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_merge_user_only_one_user(member):
    with pytest.raises(CommandError) as e:
        call_command('merge_user', 'member')
    assert "too few arguments" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_merge_user_nofrom(member2):
    with pytest.raises(CommandError) as e:
        call_command('merge_user', 'not_a_user', 'member2')
    assert "User not_a_user does not exist" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_merge_user_noto(member):
    with pytest.raises(CommandError) as e:
        call_command('merge_user', 'member', 'not_a_user2')
    assert "User not_a_user2 does not exist" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_merge_user_withdelete(capfd, member, member2):
    call_command('merge_user', 'member', 'member2')
    out, err = capfd.readouterr()
    assert 'User merged: member --> member2' in out
    assert 'Deleting user: member...' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_merge_user_nodelete(capfd, member, member2):
    call_command('merge_user', '--no-delete', 'member', 'member2')
    out, err = capfd.readouterr()
    assert 'User merged: member --> member2' in out
    assert 'Deleting user: member...' not in out

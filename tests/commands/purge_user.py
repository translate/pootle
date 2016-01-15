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
def test_purge_user_nouser():
    with pytest.raises(CommandError) as e:
        call_command('purge_user')
    assert "too few arguments" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_purge_user_single_user(capfd, evil_member):
    call_command('purge_user', 'evil_member')
    out, err = capfd.readouterr()
    assert "User purged: evil_member" in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_purge_user_multiple_users(capfd, member, member2):
    call_command('purge_user', 'member', 'member2')
    out, err = capfd.readouterr()
    assert "User purged: member " in out
    assert "User purged: member2 " in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_purge_user_unkownuser():
    with pytest.raises(CommandError) as e:
        call_command('purge_user', 'not_a_user')
    assert "User not_a_user does not exist" in str(e)

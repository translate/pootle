# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from mock import patch

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.cmd
def test_cmd_purge_user_nouser():
    with pytest.raises(CommandError) as e:
        call_command('purge_user')
    assert "too few arguments" in str(e)


@pytest.mark.cmd
@patch('accounts.management.commands.purge_user.Command.get_user')
def test_cmd_purge_user(get_user_mock):
    call_command('purge_user', 'evil_member')
    assert (
        list(get_user_mock.call_args)
        == [(u'evil_member',), {}])
    assert (
        list(get_user_mock.return_value.delete.call_args)
        == [(), {'purge': True}])

    get_user_mock.reset_mock()

    call_command('purge_user', 'evil_member', 'eviler_member')
    assert (
        [list(l) for l in get_user_mock.call_args_list]
        == [[(u'evil_member',), {}], [(u'eviler_member',), {}]])
    assert (
        list(get_user_mock.return_value.delete.call_args)
        == [(), {'purge': True}])

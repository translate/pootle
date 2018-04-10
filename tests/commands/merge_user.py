# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from mock import MagicMock, patch

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.cmd
def test_cmd_merge_user_nousers():
    with pytest.raises(CommandError) as e:
        call_command('merge_user')
    assert "too few arguments" in str(e)

    with pytest.raises(CommandError) as e:
        call_command('merge_user', 'memberX')
    assert "too few arguments" in str(e)


@pytest.mark.cmd
@patch('accounts.management.commands.merge_user.Command.get_user')
@patch('accounts.management.commands.merge_user.utils')
def test_cmd_merge_user(utils_mock, get_user_mock):
    user_mock = MagicMock()
    stdout = MagicMock()

    def _get_user(**kwargs):
        user_mock.return_value.username = kwargs['username']
        return user_mock(**kwargs)

    get_user_mock.side_effect = _get_user
    call_command('merge_user', 'memberX', 'memberY', stdout=stdout)
    assert (
        [list(l) for l in get_user_mock.call_args_list]
        == [[(), {'username': u'memberX'}],
            [(), {'username': u'memberY'}]])
    assert (
        [list(l) for l in user_mock.call_args_list]
        == [[(), {'username': u'memberX'}],
            [(), {'username': u'memberY'}]])
    assert (
        list(utils_mock.UserMerger.call_args)
        == [(user_mock.return_value, user_mock.return_value), {}])
    assert (
        list(user_mock.return_value.delete.call_args)
        == [(), {}])
    assert (
        [list(l) for l in stdout.write.call_args_list]
        == [[('Deleting user: memberY...\n',), {}],
            [('User deleted: memberY\n',), {}]])


@pytest.mark.cmd
@patch('accounts.management.commands.merge_user.Command.get_user')
@patch('accounts.management.commands.merge_user.utils')
def test_cmd_merge_user_no_delete(utils_mock, get_user_mock):
    user_mock = MagicMock()
    stdout = MagicMock()

    def _get_user(**kwargs):
        user_mock.return_value.username = kwargs['username']
        return user_mock(**kwargs)

    get_user_mock.side_effect = _get_user
    call_command(
        'merge_user', 'memberX', 'memberY', '--no-delete', stdout=stdout)
    assert (
        [list(l) for l in get_user_mock.call_args_list]
        == [[(), {'username': u'memberX'}],
            [(), {'username': u'memberY'}]])
    assert (
        [list(l) for l in user_mock.call_args_list]
        == [[(), {'username': u'memberX'}],
            [(), {'username': u'memberY'}]])
    assert (
        list(utils_mock.UserMerger.call_args)
        == [(user_mock.return_value, user_mock.return_value), {}])
    assert not user_mock.return_value.delete.called
    assert not stdout.write.called

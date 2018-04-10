# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from mock import MagicMock, patch

import pytest

from pootle_app.management.commands import PootleCommand
from pootle_app.management.commands.sync_stores import Command


@pytest.mark.cmd
@patch('pootle_app.management.commands.sync_stores.FSPlugin')
@patch('pootle_app.management.commands.sync_stores.logger')
def test_cmd_sync_stores(logger_mock, fs_plugin_mock):
    """Site wide sync_stores"""
    assert issubclass(Command, PootleCommand)
    tp = MagicMock(**{'project.pk': 23, 'pootle_path': 'FOO'})
    fs_plugin_mock.return_value.state.return_value = [
        'pootle_updated', 'fs_updated']
    command = Command()
    command.handle_all_stores(tp, skip_missing=True)
    assert (
        list(fs_plugin_mock.call_args)
        == [(tp.project,), {}])
    assert (
        list(fs_plugin_mock.return_value.fetch.call_args())
        == ['', (), {}])
    assert (
        list(fs_plugin_mock.return_value.state.call_args())
        == ['', (), {}])
    assert (
        list(fs_plugin_mock.return_value.sync.call_args)
        == [(), {'pootle_path': 'FOO*', 'update': 'fs'}])
    assert not logger_mock.warn.called
    assert not fs_plugin_mock.return_value.add.called
    assert command.warn_on_conflict == []


@pytest.mark.cmd
@patch('pootle_app.management.commands.sync_stores.FSPlugin')
@patch('pootle_app.management.commands.sync_stores.logger')
def test_cmd_sync_stores_skip_missing(logger_mock, fs_plugin_mock):
    """Site wide sync_stores"""
    assert issubclass(Command, PootleCommand)
    tp = MagicMock(**{'project.pk': 23, 'pootle_path': 'FOO'})
    fs_plugin_mock.return_value.state.return_value = [
        'pootle_updated', 'fs_updated']
    command = Command()
    command.handle_all_stores(tp, skip_missing=False)
    assert (
        list(fs_plugin_mock.call_args)
        == [(tp.project,), {}])
    assert (
        list(fs_plugin_mock.return_value.fetch.call_args())
        == ['', (), {}])
    assert (
        list(fs_plugin_mock.return_value.state.call_args())
        == ['', (), {}])
    assert (
        list(fs_plugin_mock.return_value.sync.call_args)
        == [(), {'pootle_path': 'FOO*', 'update': 'fs'}])
    assert not logger_mock.warn.called
    assert (
        list(fs_plugin_mock.return_value.add.call_args)
        == [(), {'pootle_path': 'FOO*', 'update': 'fs'}])
    assert command.warn_on_conflict == []


@pytest.mark.cmd
@patch('pootle_app.management.commands.sync_stores.FSPlugin')
@patch('pootle_app.management.commands.sync_stores.logger')
def test_cmd_sync_stores_warn_on_conflict(logger_mock, fs_plugin_mock):
    """Site wide sync_stores"""
    assert issubclass(Command, PootleCommand)
    tp = MagicMock(
        **{'project.code': 7,
           'project.pk': 23,
           'pootle_path': 'FOO'})
    fs_plugin_mock.return_value.state.return_value = [
        'pootle_updated', 'conflict_untracked']
    command = Command()
    command.handle_all_stores(tp, skip_missing=True)
    assert (
        list(fs_plugin_mock.call_args)
        == [(tp.project,), {}])
    assert (
        list(fs_plugin_mock.return_value.fetch.call_args())
        == ['', (), {}])
    assert (
        list(fs_plugin_mock.return_value.state.call_args())
        == ['', (), {}])
    assert (
        list(fs_plugin_mock.return_value.sync.call_args)
        == [(), {'pootle_path': 'FOO*', 'update': 'fs'}])
    assert (
        list(logger_mock.warn.call_args)
        == [("The project '%s' has conflicting changes in the database "
             "and translation files. Use `pootle fs resolve` to tell "
             "pootle how to merge", 7), {}])
    assert not fs_plugin_mock.return_value.add.called
    assert command.warn_on_conflict == [23]


@pytest.mark.cmd
@patch('pootle_app.management.commands.sync_stores.PootleCommand.handle')
@patch('pootle_app.management.commands.sync_stores.logger')
def test_cmd_sync_stores_warn(logger_mock, super_mock):
    command = Command()
    kwargs = dict(force=False, overwrite=False, foo='bar')
    command.handle(**kwargs)
    assert (
        list(logger_mock.warn.call_args)
        == [('The sync_stores command is deprecated, use pootle fs instead',),
            {}])
    assert (
        list(super_mock.call_args)
        == [(), kwargs])

    logger_mock.reset_mock()
    super_mock.reset_mock()
    kwargs['force'] = True
    command.handle(**kwargs)
    assert (
        [list(l) for l in logger_mock.warn.call_args_list]
        == [[('The sync_stores command is deprecated, use pootle fs instead',),
             {}],
            [('The force option no longer has any affect on this command',),
             {}]])
    assert (
        list(super_mock.call_args)
        == [(), kwargs])

    logger_mock.reset_mock()
    super_mock.reset_mock()
    kwargs['force'] = False
    kwargs['overwrite'] = True
    command.handle(**kwargs)
    assert (
        [list(l) for l in logger_mock.warn.call_args_list]
        == [[('The sync_stores command is deprecated, use pootle fs instead',),
             {}],
            [('The overwrite option no longer has any affect on this command',),
             {}]])
    assert (
        list(super_mock.call_args)
        == [(), kwargs])

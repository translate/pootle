# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from mock import PropertyMock, patch

import pytest

from django.core.management import CommandError, call_command

from pootle_app.management.commands.update_stores import Command


# TODO: add test for _create_tps_for_projects/_parse_tps_to_create


DEFAULT_OPTIONS = {
    'force': False,
    'settings': None,
    'pythonpath': None,
    'verbosity': 3,
    'traceback': False,
    u'skip_checks': True,
    'no_rq': False,
    'atomic': 'tp',
    'noinput': False,
    'overwrite': False,
    'no_color': False}


@pytest.mark.cmd
@patch('pootle_app.management.commands.PootleCommand.handle_all')
@patch(
    'pootle_app.management.commands.update_stores.Project.objects',
    new_callable=PropertyMock)
@patch(
    'pootle_app.management.commands.update_stores.Command._create_tps_for_project')
@patch(
    'pootle_app.management.commands.update_stores.Command.check_projects')
def test_update_stores_noargs(check_projects, create_mock, project_mock,
                              command_mock, capfd):
    """Site wide update_stores"""
    project_mock.configure_mock(
        **{"return_value.all.return_value.iterator.return_value": [1, 2, 3],
           "return_value.filter.return_value.iterator.return_value": [4, 5, 6]})
    command_mock.return_value = 23
    call_command('update_stores', '-v3')

    assert (
        [list(l) for l in create_mock.call_args_list]
        == [[(1,), {}], [(2,), {}], [(3,), {}]])

    assert (
        list(command_mock.call_args)
        == [(), DEFAULT_OPTIONS])

    create_mock.reset_mock()
    command_mock.reset_mock()

    call_command('update_stores', '-v3', '--project', '7', '--project', '23')
    assert (
        list(check_projects.call_args)
        == [([u'7', u'23'],), {}])
    assert (
        [list(l) for l in create_mock.call_args_list]
        == [[(4,), {}], [(5,), {}], [(6,), {}]])
    assert (
        list(command_mock.call_args)
        == [(), DEFAULT_OPTIONS])


@pytest.mark.cmd
@patch('pootle_app.management.commands.update_stores.FSPlugin')
def test_update_stores_tp(plugin_mock):
    """Site wide update_stores"""
    command = Command()
    tp = PropertyMock()
    tp.configure_mock(
        **{'pootle_path': 'FOO',
           'project': 23})
    command.handle_translation_project(tp, **DEFAULT_OPTIONS)
    assert (
        list(plugin_mock.return_value.add.call_args)
        == [(), {'pootle_path': 'FOO*', 'update': 'pootle'}])
    assert (
        list(plugin_mock.return_value.rm.call_args)
        == [(), {'pootle_path': 'FOO*', 'update': 'pootle'}])
    assert (
        list(plugin_mock.return_value.resolve.call_args)
        == [(), {'pootle_path': 'FOO*', 'merge': True}])
    assert (
        list(plugin_mock.return_value.sync.call_args)
        == [(), {'pootle_path': 'FOO*', 'update': 'pootle'}])
    assert list(plugin_mock.call_args) == [(23,), {}]


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_stores_non_existent_lang_or_proj():
    with pytest.raises(CommandError):
        call_command("update_stores", "--project", "non_existent_project")
    with pytest.raises(CommandError):
        call_command("update_stores", "--language", "non_existent_language")

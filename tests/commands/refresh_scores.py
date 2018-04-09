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

from pootle_app.management.commands.refresh_scores import Command
from pootle_translationproject.models import TranslationProject


DEFAULT_OPTIONS = {
    'reset': False,
    'users': None,
    'settings': None,
    'pythonpath': None,
    'verbosity': 1,
    'traceback': False,
    u'skip_checks': True,
    'no_rq': False,
    'atomic': 'tp',
    'noinput': False,
    'no_color': False}


@pytest.mark.cmd
@patch('pootle_app.management.commands.refresh_scores.get_user_model')
@patch('pootle_app.management.commands.refresh_scores.Command.get_users')
@patch('pootle_app.management.commands.refresh_scores.score_updater')
def test_cmd_refresh_scores_recalculate(updater_mock, users_mock, user_mock):
    """Recalculate scores."""
    user_mock.return_value = 7
    users_mock.return_value = 23
    call_command('refresh_scores')
    assert (
        list(users_mock.call_args)
        == [(), DEFAULT_OPTIONS])
    assert (
        list(updater_mock.get.call_args)
        == [(7,), {}])
    assert (
        list(updater_mock.get.return_value.call_args)
        == [(), {}])
    assert (
        list(updater_mock.get.return_value.return_value.refresh_scores.call_args)
        == [(23,), {}])


@pytest.mark.cmd
@patch('pootle_app.management.commands.refresh_scores.get_user_model')
@patch('pootle_app.management.commands.refresh_scores.Command.get_users')
@patch('pootle_app.management.commands.refresh_scores.score_updater')
def test_cmd_refresh_scores_recalculate_user(updater_mock, users_mock, user_mock):
    """Recalculate scores for given users."""
    user_mock.return_value = 7
    users_mock.return_value = 23
    call_command('refresh_scores', '--user=member')
    options = DEFAULT_OPTIONS.copy()
    options["users"] = ["member"]
    assert (
        list(users_mock.call_args)
        == [(), options])
    assert (
        list(updater_mock.get.call_args)
        == [(7,), {}])
    assert (
        list(updater_mock.get.return_value.call_args)
        == [(), {}])
    assert (
        list(updater_mock.get.return_value.return_value.refresh_scores.call_args)
        == [(23,), {}])


@pytest.mark.cmd
@patch('pootle_app.management.commands.refresh_scores.get_user_model')
@patch('pootle_app.management.commands.refresh_scores.Command.get_users')
@patch('pootle_app.management.commands.refresh_scores.score_updater')
def test_cmd_refresh_scores_reset_user(updater_mock, users_mock, user_mock):
    """Set scores to zero for given users."""
    user_mock.return_value = 7
    users_mock.return_value = 23
    call_command('refresh_scores', '--reset', '--user=member')
    options = DEFAULT_OPTIONS.copy()
    options["users"] = ["member"]
    options["reset"] = True
    assert (
        list(users_mock.call_args)
        == [(), options])
    assert (
        list(updater_mock.get.call_args)
        == [(7,), {}])
    assert (
        list(updater_mock.get.return_value.call_args)
        == [(), {'users': 23}])
    assert (
        list(updater_mock.get.return_value.return_value.clear.call_args)
        == [(), {}])


@pytest.mark.cmd
@patch('pootle_app.management.commands.refresh_scores.get_user_model')
@patch('pootle_app.management.commands.refresh_scores.Command.get_users')
@patch('pootle_app.management.commands.refresh_scores.score_updater')
def test_cmd_refresh_scores_reset(updater_mock, users_mock, user_mock):
    """Set scores to zero."""
    user_mock.return_value = 7
    users_mock.return_value = 23
    call_command('refresh_scores', '--reset')
    options = DEFAULT_OPTIONS.copy()
    options["reset"] = True
    assert (
        list(users_mock.call_args)
        == [(), options])
    assert (
        list(updater_mock.get.call_args)
        == [(7,), {}])
    assert (
        list(updater_mock.get.return_value.call_args)
        == [(), {'users': 23}])
    assert (
        list(updater_mock.get.return_value.return_value.clear.call_args)
        == [(), {}])


@pytest.mark.cmd
@patch('pootle_app.management.commands.PootleCommand.handle_all')
@patch('pootle_app.management.commands.refresh_scores.Command.check_projects')
def test_cmd_refresh_scores_project(projects_mock, command_mock):
    """Reset and set again scores for a project."""

    call_command('refresh_scores', '--reset', '--project=project0')
    options = DEFAULT_OPTIONS.copy()
    options["reset"] = True
    assert (
        list(projects_mock.call_args)
        == [([u'project0'],), {}])
    assert (
        list(command_mock.call_args)
        == [(), options])
    projects_mock.reset_mock()
    command_mock.reset_mock()
    call_command('refresh_scores', '--project=project0')
    assert (
        list(projects_mock.call_args)
        == [([u'project0'],), {}])
    assert (
        list(command_mock.call_args)
        == [(), DEFAULT_OPTIONS])


@pytest.mark.cmd
@patch('pootle_app.management.commands.PootleCommand.handle_all')
@patch('pootle_app.management.commands.refresh_scores.Command.check_languages')
def test_cmd_refresh_scores_language(languages_mock, command_mock):
    """Reset and set again scores for a language."""

    call_command('refresh_scores', '--reset', '--language=language0')
    assert (
        list(languages_mock.call_args)
        == [([u'language0'],), {}])
    options = DEFAULT_OPTIONS.copy()
    options["reset"] = True
    assert (
        list(command_mock.call_args)
        == [(), options])

    languages_mock.reset_mock()
    command_mock.reset_mock()
    call_command('refresh_scores', '--language=language0')
    assert (
        list(languages_mock.call_args)
        == [([u'language0'],), {}])
    assert (
        list(command_mock.call_args)
        == [(), DEFAULT_OPTIONS])


@pytest.mark.cmd
@patch('pootle_app.management.commands.PootleCommand.handle_all')
@patch('pootle_app.management.commands.refresh_scores.Command.check_projects')
@patch('pootle_app.management.commands.refresh_scores.Command.check_languages')
def test_cmd_refresh_scores_reset_tp(languages_mock, projects_mock, command_mock):
    """Reset and set again scores for a TP."""

    call_command(
        'refresh_scores',
        '--reset',
        '--language=language0',
        '--project=project0')
    assert (
        list(languages_mock.call_args)
        == [([u'language0'],), {}])
    assert (
        list(projects_mock.call_args)
        == [([u'project0'],), {}])
    options = DEFAULT_OPTIONS.copy()
    options["reset"] = True
    assert (
        list(command_mock.call_args)
        == [(), options])

    languages_mock.reset_mock()
    projects_mock.reset_mock()
    command_mock.reset_mock()
    call_command(
        'refresh_scores',
        '--language=language0',
        '--project=project0')
    assert (
        list(languages_mock.call_args)
        == [([u'language0'],), {}])
    assert (
        list(projects_mock.call_args)
        == [([u'project0'],), {}])
    assert (
        list(command_mock.call_args)
        == [(), DEFAULT_OPTIONS])


@pytest.mark.cmd
@patch('pootle_app.management.commands.PootleCommand.handle_all')
@patch('pootle_app.management.commands.refresh_scores.Command.check_languages')
def test_cmd_refresh_scores_user_language(languages_mock, command_mock):
    """Reset and set again scores for particular user in language."""
    call_command(
        'refresh_scores',
        '--user=member',
        '--language=language0')
    options = DEFAULT_OPTIONS.copy()
    options["users"] = ["member"]
    assert (
        list(languages_mock.call_args)
        == [([u'language0'],), {}])
    assert (
        list(command_mock.call_args)
        == [(), options])
    languages_mock.reset_mock()
    command_mock.reset_mock()
    call_command(
        'refresh_scores',
        '--reset',
        '--user=member',
        '--language=language0')
    options["reset"] = True
    assert (
        list(languages_mock.call_args)
        == [([u'language0'],), {}])
    assert (
        list(command_mock.call_args)
        == [(), options])


@pytest.mark.cmd
@patch('pootle_app.management.commands.PootleCommand.handle_all')
@patch('pootle_app.management.commands.refresh_scores.Command.check_projects')
def test_cmd_refresh_scores_user_project(projects_mock, command_mock):
    """Reset and set again scores for particular user in project."""
    call_command(
        'refresh_scores',
        '--user=member',
        '--project=project0')
    options = DEFAULT_OPTIONS.copy()
    options["users"] = ["member"]
    assert (
        list(projects_mock.call_args)
        == [([u'project0'],), {}])
    assert (
        list(command_mock.call_args)
        == [(), options])
    projects_mock.reset_mock()
    command_mock.reset_mock()
    call_command(
        'refresh_scores',
        '--reset',
        '--user=member',
        '--project=project0')
    options["reset"] = True
    assert (
        list(projects_mock.call_args)
        == [([u'project0'],), {}])
    assert (
        list(command_mock.call_args)
        == [(), options])


@pytest.mark.cmd
@patch('pootle_app.management.commands.PootleCommand.handle_all')
@patch('pootle_app.management.commands.refresh_scores.Command.check_languages')
@patch('pootle_app.management.commands.refresh_scores.Command.check_projects')
def test_cmd_refresh_scores_user_tp(projects_mock, languages_mock, command_mock):
    """Reset and set again scores for particular user in project."""
    call_command(
        'refresh_scores',
        '--user=member',
        '--language=language0',
        '--project=project0')
    options = DEFAULT_OPTIONS.copy()
    options["users"] = ["member"]
    assert (
        list(projects_mock.call_args)
        == [([u'project0'],), {}])
    assert (
        list(languages_mock.call_args)
        == [([u'language0'],), {}])
    assert (
        list(command_mock.call_args)
        == [(), options])
    languages_mock.reset_mock()
    projects_mock.reset_mock()
    command_mock.reset_mock()
    call_command(
        'refresh_scores',
        '--reset',
        '--user=member',
        '--language=language0',
        '--project=project0')
    options["reset"] = True
    assert (
        list(projects_mock.call_args)
        == [([u'project0'],), {}])
    assert (
        list(languages_mock.call_args)
        == [([u'language0'],), {}])
    assert (
        list(command_mock.call_args)
        == [(), options])


@pytest.mark.cmd
@patch('pootle_app.management.commands.refresh_scores.get_user_model')
def test_cmd_refresh_scores_get_users(user_mock):
    user_mock.configure_mock(
        **{'return_value.objects.filter.return_value.values_list.return_value':
           (1, 2, 3)})
    command = Command()
    assert command.get_users(users=None) is None
    assert not user_mock.called

    assert command.get_users(users="FOO") == [1, 2, 3]
    assert (
        list(user_mock.call_args)
        == [(), {}])
    user_filter = user_mock.return_value.objects.filter
    assert (
        list(user_filter.call_args)
        == [(), {'username__in': 'FOO'}])
    assert (
        list(user_filter.return_value.values_list.call_args)
        == [('pk',), {'flat': True}])


@pytest.mark.cmd
@patch('pootle_app.management.commands.refresh_scores.Command.get_users')
@patch('pootle_app.management.commands.refresh_scores.score_updater')
def test_cmd_refresh_scores_handle_all_stores(updater_mock, users_mock):
    users_mock.return_value = 7
    command = Command()
    command.handle_all_stores("FOO", reset=False)
    assert (
        list(users_mock.call_args)
        == [(), {'reset': False}])
    assert (
        list(updater_mock.get.call_args)
        == [(TranslationProject,), {}])
    assert (
        list(updater_mock.get.return_value.call_args)
        == [('FOO',), {}])
    assert (
        list(updater_mock.get.return_value.call_args)
        == [('FOO',), {}])
    assert (
        list(updater_mock.get.return_value.return_value.refresh_scores.call_args)
        == [(7,), {}])

    command.handle_all_stores("FOO", reset=True)
    assert (
        list(users_mock.call_args)
        == [(), {'reset': True}])
    assert (
        list(updater_mock.get.call_args)
        == [(TranslationProject,), {}])
    assert (
        list(updater_mock.get.return_value.call_args)
        == [('FOO',), {}])
    assert (
        list(updater_mock.get.return_value.call_args)
        == [('FOO',), {}])
    assert (
        list(updater_mock.get.return_value.return_value.clear.call_args)
        == [(7,), {}])

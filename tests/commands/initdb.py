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

from pootle_app.management.commands import SkipChecksMixin
from pootle_app.management.commands.initdb import Command


@pytest.mark.cmd
def test_cmd_initdb_skip_checks():
    assert issubclass(Command, SkipChecksMixin)


@pytest.mark.cmd
@patch('pootle_app.management.commands.initdb.InitDB')
def test_cmd_initdb_noprojects(init_mock):
    """Initialise the database with initdb
    """
    stdout = MagicMock()
    call_command('initdb', '--no-projects', stdout=stdout)
    assert (
        [list(l) for l in stdout.write.call_args_list]
        == [[('Populating the database.\n',), {}],
            [('Successfully populated the database.\n',), {}],
            [('To create an admin user, use the `pootle createsuperuser` '
              'command.\n',),
             {}]])
    assert (
        list(init_mock.call_args)
        == [(), {}])
    assert (
        list(init_mock.return_value.init_db.call_args)
        == [(False,), {}])


@pytest.mark.cmd
@patch('pootle_app.management.commands.initdb.InitDB')
def test_cmd_initdb_projects(init_mock):
    """Initialise the database with initdb
    """
    stdout = MagicMock()
    call_command('initdb', stdout=stdout)
    assert (
        [list(l) for l in stdout.write.call_args_list]
        == [[('Populating the database.\n',), {}],
            [('Successfully populated the database.\n',), {}],
            [('To create an admin user, use the `pootle createsuperuser` '
              'command.\n',),
             {}]])
    assert (
        list(init_mock.call_args)
        == [(), {}])
    assert (
        list(init_mock.return_value.init_db.call_args)
        == [(True,), {}])

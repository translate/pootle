# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command, get_commands

CORE_APPS_WITH_COMMANDS = (
    'accounts', 'pootle_app', 'import_export', 'virtualfolder',
)


@pytest.mark.cmd
@pytest.mark.parametrize("command,app", [
    (command, app)
    for command, app in get_commands().iteritems()
    if app.startswith('pootle_') or app in CORE_APPS_WITH_COMMANDS
])
def test_initdb_help(capfd, command, app):
    """Catch any simple command issues"""
    print("Command: %s, App: %s" % (command, app))
    with pytest.raises(SystemExit):
        call_command(command, '--help')
    out, err = capfd.readouterr()
    assert '--help' in out

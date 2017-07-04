# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from subprocess import call

import pytest


pytestmark = pytest.mark.skipif(call(['which', 'pootle']) != 0,
                                reason='not installed via setup.py')


@pytest.mark.cmd
def test_pootle_noargs(capfd):
    """Pootle no args should give help"""
    call(['pootle'])
    out, err = capfd.readouterr()
    # Expected:
    #   Type 'pootle help <subcommand>'
    # but 'pootle' is 'pootle-script.py' on Windows
    assert "Type 'pootle" in out
    assert " help <subcommand>'" in out


@pytest.mark.cmd
def test_pootle_version(capfd):
    """Display Pootle version info"""
    call(['pootle', '--version'])
    out, err = capfd.readouterr()
    assert 'Pootle' in err
    assert 'Django' in err
    assert 'Translate Toolkit' in err


@pytest.mark.cmd
def test_pootle_init(capfd):
    """pootle init --help"""
    call(['pootle', 'init', '--help'])
    out, err = capfd.readouterr()
    assert "--db" in out


@pytest.mark.cmd
def test_pootle_init_db_sqlite(capsys, tmpdir):
    """pootle init --help"""
    test_conf_file = tmpdir.join("pootle.conf")
    assert not os.path.exists(str(test_conf_file))
    call(['pootle', 'init', '--db=sqlite', '--config=%s' % test_conf_file])
    assert os.path.exists(str(test_conf_file))

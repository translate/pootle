# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from subprocess import call

import pytest


@pytest.mark.cmd
def test_manage_noargs(capfd):
    """./manage.py with no args should give help"""
    call(['./manage.py'])
    out, err = capfd.readouterr()
    assert "Available subcommands:" in out


@pytest.mark.cmd
def test_manage_revision(capfd):
    """./manage.py revision, just to see that a simple command works."""
    call(['./manage.py', 'revision'])
    out, err = capfd.readouterr()
    assert out.rstrip().isnumeric()

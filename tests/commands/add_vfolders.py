# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.cmd
def test_add_vfolders_user_nofile():
    """Missing vfolder argument."""
    with pytest.raises(CommandError) as e:
        call_command('add_vfolders')
    assert "too few arguments" in str(e)


@pytest.mark.cmd
def test_add_vfolders_user_non_existant_file():
    """No file on filesystem."""
    with pytest.raises(CommandError) as e:
        call_command('add_vfolders', 'nofile.json')
    assert "No such file or directory" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_add_vfolders_emptyfile(capfd, tmpdir):
    """Load an empty vfolder.json file"""
    p = tmpdir.mkdir("sub").join("empty.json")
    p.write("{}")
    call_command('add_vfolders', os.path.join(p.dirname, p.basename))
    out, err = capfd.readouterr()
    assert "Importing virtual folders" in out

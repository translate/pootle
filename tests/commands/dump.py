# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command
from django.core.management.base import CommandError


@pytest.mark.cmd
@pytest.mark.django_db
def test_dump_noargs():
    """Dump requires an output option."""
    with pytest.raises(CommandError) as e:
        call_command('dump')
    assert "Set --data or --stats option" in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_dump_data(capfd):
    """--data output."""
    call_command('dump', '--data')
    out, err = capfd.readouterr()
    assert "Directory" in out
    assert "Project" in out
    assert "TranslationProject" in out
    assert "Store" in out
    # FIXME unsure why this one does not appear
    # assert "Language" in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_dump_stats(capfd):
    """--stats output."""
    call_command('dump', '--stats')
    out, err = capfd.readouterr()
    # Ensure it's a --stats
    assert 'None,None' in out
    assert out.startswith('/')
    # Ensure its got all the files, the data differs due to differing load
    # sequences
    # First level
    assert '/language0/project0/' in out
    assert '/language1/project0/' in out
    assert '/projects/project0/' in out
    # Deeper levels in output
    assert '/language0/project0/store0.po' in out
    assert '/language0/project0/subdir0' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_dump_stop_level(capfd):
    """Set the depth for data."""
    call_command('dump', '--stats', '--stop-level=1')
    out, err = capfd.readouterr()
    # Ensure it's a --stats
    assert 'None,None' in out
    assert out.startswith('/')

    # First level
    assert '/language0/project0/' in out
    assert '/language1/project0/' in out
    assert '/projects/project0/' in out
    # Deeper levels not output
    assert '/language0/project0/store0.po' not in out
    assert '/language0/project0/subdir0' not in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_dump_data_tp(capfd):
    """--data output with TP selection."""
    call_command('dump', '--data', '--project=project0', '--language=language0')
    out, err = capfd.readouterr()
    assert "Directory" in out
    assert "Store" in out
    # FIXME check if these really should be missing
    assert "Language" not in out
    assert "Project" not in out
    assert "TranslationProject" not in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_dump_stats_tp(capfd):
    """--stats output with TP selection"""

    call_command('dump', '--stats', '--project=project0', '--language=language0')
    out, err = capfd.readouterr()
    # Ensure it's a --stats
    stats_match = out.split("\n")[0].strip().split(" ").pop()
    assert "None,None" in stats_match
    assert out.startswith('/')
    # Ensure its got all the files (the data differs due to differing load
    # sequences)
    # First level
    assert '/language0/project0/' in out
    # Deaper levels not output
    assert '/language0/project0/store0.po' in out
    assert '/language0/project0/subdir0' in out

    assert '/projects/project0/' not in out
    assert '/language1/project0/' not in out

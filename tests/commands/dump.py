# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import re

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
def test_dump_data(capfd, afrikaans_tutorial):
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
def test_dump_stats(capfd, afrikaans_tutorial):
    """--stats output."""
    call_command('dump', '--stats')
    out, err = capfd.readouterr()
    # Ensure it's a --stats
    assert 'None,None' in out
    assert out.startswith('/')
    # Ensure its got all the files, the data differs due to differing load
    # sequences
    assert '/af/tutorial/issue_2401.po' in out
    assert '/af/tutorial/test_get_units.po' in out
    assert '/af/tutorial/' in out
    assert '/af/tutorial/subdir/' in out
    assert '/projects/tutorial/' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_dump_stop_level(capfd, afrikaans_tutorial):
    """Set the depth for data."""
    call_command('dump', '--stats', '--stop-level=1')
    out, err = capfd.readouterr()
    # Ensure it's a --stats
    assert 'None,None' in out
    assert out.startswith('/')
    # First level
    assert '/af/tutorial/' in out
    assert '/projects/tutorial/' in out
    # Deaper levels not output
    assert '/af/tutorial/issue_2401.po' not in out
    assert '/af/tutorial/test_get_units.po' not in out
    assert '/af/tutorial/subdir/' not in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_dump_data_tp(capfd, afrikaans_tutorial):
    """--data output with TP selection."""
    call_command('dump', '--data', '--project=tutorial', '--language=af')
    out, err = capfd.readouterr()
    assert "Directory" in out
    assert "Store" in out
    # FIXME check if these really should be missing
    assert "Language" not in out
    assert "Project" not in out
    assert "TranslationProject" not in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_dump_stats_tp(capfd, afrikaans_tutorial):
    """--stats output with TP selection"""

    call_command('dump', '--stats', '--project=tutorial', '--language=af')
    out, err = capfd.readouterr()
    # Ensure it's a --stats
    stats_match = out.split("\n")[0].strip().split(" ").pop()
    assert re.match(r"\d+,\d+,\d+", stats_match)
    assert out.startswith('/')
    # Ensure its got all the files (the data differs due to differing load
    # sequences)
    assert '/af/tutorial/issue_2401.po' in out
    assert '/af/tutorial/test_get_units.po' in out
    assert '/af/tutorial/' in out
    assert '/af/tutorial/subdir/' in out
    # As this is a TP, these shouldn't be here
    assert '/projects/tutorial/' not in out

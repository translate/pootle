# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_recalculate(capfd):
    """Recalculate scores."""
    call_command('refresh_scores')
    out, err = capfd.readouterr()
    assert 'Score for user system set to' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_recalculate_user(capfd):
    """Recalculate scores for given users."""
    call_command('refresh_scores', '--user=system')
    out, err = capfd.readouterr()
    assert 'Score for user system set to' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_reset_user(capfd):
    """Set scores to zero for given users."""
    call_command('refresh_scores', '--reset', '--user=system')
    out, err = capfd.readouterr()
    assert 'Scores for specified users were reset to 0.' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_refresh_scores_reset(capfd):
    """Set scores to zero."""
    call_command('refresh_scores', '--reset')
    out, err = capfd.readouterr()
    assert 'Scores for all users were reset to 0.' in out

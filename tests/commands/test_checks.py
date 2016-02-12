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

from pootle_store.models import Unit, TRANSLATED


@pytest.mark.cmd
def test_test_checks_noargs():
    """No args should fail wanting either --unit or --source."""
    with pytest.raises(CommandError) as e:
        call_command('test_checks')
    assert ("Either --unit or a pair of --source and "
            "--target must be provided." in str(e))


@pytest.mark.cmd
@pytest.mark.django_db
def test_test_checks_unit_unkown(afrikaans_tutorial):
    """Check a --unit that we won't have"""
    with pytest.raises(CommandError) as e:
        call_command('test_checks', '--unit=100000')
    assert 'Unit matching query does not exist' in str(e)


@pytest.mark.cmd
@pytest.mark.django_db
def test_test_checks_unit(capfd):
    """Check a --unit"""

    units = Unit.objects.filter(
        state=TRANSLATED,
        target_f__endswith="%s.")
    call_command('test_checks', '--unit=%s' % units.first().id)
    out, err = capfd.readouterr()
    assert 'No errors found' in out


@pytest.mark.cmd
def test_test_checks_srctgt_missing_args():
    """Check a --source --target with incomplete options."""
    with pytest.raises(CommandError) as e:
        call_command('test_checks', '--source="files"')
    assert 'Use a pair of --source and --target' in str(e)
    with pytest.raises(CommandError) as e:
        call_command('test_checks', '--target="leers"')
    assert 'Use a pair of --source and --target' in str(e)


@pytest.mark.cmd
def test_test_checks_srctgt_pass(capfd):
    """Passing --source --target check."""
    call_command('test_checks', '--source="Files"', '--target="Leers"')
    out, err = capfd.readouterr()
    assert 'No errors found' in out


@pytest.mark.cmd
def test_test_checks_srctgt_fail(capfd):
    """Failing --source --target check."""
    call_command('test_checks', '--source="%s files"', '--target="%s leers"')
    out, err = capfd.readouterr()
    assert 'No errors found' in out
    call_command('test_checks', '--source="%s files"', '--target="%d leers"')
    out, err = capfd.readouterr()
    assert 'Failing checks' in out


@pytest.mark.cmd
def test_test_checks_alt_checker(capfd, settings):
    """Use an alternate checker."""
    settings.POOTLE_QUALITY_CHECKER = 'pootle_misc.checks.ENChecker'
    call_command('test_checks', '--source="%s files"', '--target="%s leers"')
    out, err = capfd.readouterr()
    assert 'No errors found' in out
    call_command('test_checks', '--source="%s files"', '--target="%d leers"')
    out, err = capfd.readouterr()
    assert 'Failing checks' in out

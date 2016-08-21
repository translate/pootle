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
def test_calculate_checks_noargs(capfd):
    call_command('calculate_checks')
    out, err = capfd.readouterr()
    assert 'Running calculate_checks (noargs)' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_calculate_checks_printf(capfd):
    call_command('calculate_checks', '--check=printf')
    out, err = capfd.readouterr()
    assert 'Running calculate_checks (noargs)' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_calculate_checks_afrikaans(capfd):
    call_command('calculate_checks', '--language=language0')
    out, err = capfd.readouterr()
    assert 'Running calculate_checks for /language0/project0/' in out

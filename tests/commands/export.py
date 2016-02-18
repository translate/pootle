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
def test_export_noargs(capfd):
    """Export whole site"""
    call_command('export')
    out, err = capfd.readouterr()
    assert 'Created project0-language0.zip' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_project(capfd):
    """Export a project"""
    call_command('export', '--project=project0')
    out, err = capfd.readouterr()
    assert 'project0.zip' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_language(capfd):
    """Export a language"""
    call_command('export', '--language=language0')
    out, err = capfd.readouterr()
    assert 'language0.zip' in out
    assert 'language1.zip' not in out

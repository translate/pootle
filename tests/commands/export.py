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
def test_export_project_and_lang(capfd):
    """Export a project TP"""
    call_command('export', '--project=project0', '--language=language0')
    out, err = capfd.readouterr()
    assert 'project0-language0.zip' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_language(capfd):
    """Export a language"""
    call_command('export', '--language=language0')
    out, err = capfd.readouterr()
    assert 'language0.zip' in out
    assert 'language1.zip' not in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_path(capfd):
    """Export a path

    Testing variants of lang, TP, single PO file and whole site.
    """
    call_command('export', '--path=/language0')
    out, err = capfd.readouterr()
    assert 'language0.zip' in out
    assert 'language1.zip' not in out

    call_command('export', '--path=/language0/project0')
    out, err = capfd.readouterr()
    assert 'language0-project0.zip' in out

    call_command('export', '--path=/language0/project0/store0.po')
    out, err = capfd.readouterr()
    assert 'store0.po' in out

    call_command('export', '--path=/')
    out, err = capfd.readouterr()
    assert 'export.zip' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_export_path_unknown():
    """Export an unknown path"""
    with pytest.raises(CommandError) as e:
        call_command('export', '--path=/af/unknown')
    assert "Could not find store matching '/af/unknown'" in str(e)

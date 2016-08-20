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
def test_list_languages(capfd):
    """Full site list of active languages"""
    call_command('list_languages')
    out, err = capfd.readouterr()
    assert 'language0' in out
    assert 'language1' in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_list_languages_project(capfd):
    """Languages on a specific project"""
    call_command('list_languages', '--project=project0')
    out, err = capfd.readouterr()
    assert 'language0' in out
    assert 'language1' in out
    assert 'en' not in out


@pytest.mark.cmd
@pytest.mark.django_db
def test_list_languages_modified_since(capfd):
    """Languages modified since a revision"""
    call_command('list_languages', '--modified-since=%d' % (3))
    out, err = capfd.readouterr()
    assert 'language0' in out
    assert 'language1' in out

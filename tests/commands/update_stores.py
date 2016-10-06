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
def test_update_stores_noargs(capfd, project0_nongnu, project1, language1):
    """Site wide update_stores"""
    # speed up test by deleting objects
    project1.delete()
    language1.delete()
    call_command('update_stores')
    out, err = capfd.readouterr()

    # Store and Unit are deleted as there are no files on disk
    # SO - Store Obsolete
    assert 'system\tSO\t/language0/project0/store0.po' in err
    # UO - Unit Obsolete
    assert 'system\tUO\tlanguage0' in err

    # Repeat and we should have zero output
    call_command('update_stores')
    out, err = capfd.readouterr()
    assert 'system\tSO' not in err
    assert 'system\tUO' not in err


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_stores_project_tree_none(capfd, project0):
    project0.treestyle = 'pootle_fs'
    project0.save()
    call_command("update_stores", "--project", project0.code)
    out, err = capfd.readouterr()
    assert not out
    assert not err

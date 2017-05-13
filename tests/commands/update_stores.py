# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import CommandError, call_command


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_stores_noargs(capfd, project0_nongnu, project1, language1):
    """Site wide update_stores"""
    call_command('update_stores', '-v3')
    out, err = capfd.readouterr()
    # Store and Unit are deleted as there are no files on disk
    # SO - Store Obsolete
    assert 'system\tSO\t/language0/project0/store0.po' in err

    # Repeat and we should have zero output
    call_command('update_stores', "-v3")
    out, err = capfd.readouterr()
    assert 'system\tSO' not in err


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_stores_project_tree_none(capfd, project0):
    project0.treestyle = 'pootle_fs'
    project0.save()
    capfd.readouterr()
    call_command(
        "update_stores", "--atomic=all", "--project", project0.code)
    out, err = capfd.readouterr()
    assert not out
    assert not err


@pytest.mark.cmd
@pytest.mark.django_db
def test_update_stores_non_existent_lang_or_proj():
    with pytest.raises(CommandError):
        call_command("update_stores", "--project", "non_existent_project")
    with pytest.raises(CommandError):
        call_command("update_stores", "--language", "non_existent_language")

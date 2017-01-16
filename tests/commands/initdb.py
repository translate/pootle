# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command

from pootle_format.models import Format
from pootle_project.models import Project


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_initdb_noprojects(capfd, no_permission_sets, no_permissions,
                               no_users, templates):
    """Initialise the database with initdb
    """
    templates.delete()
    call_command('initdb', '--no-projects')
    out, err = capfd.readouterr()
    assert "Successfully populated the database." in out
    assert "pootle createsuperuser" in out
    # FIXME ideally we want to check for these but it seems that test oders and
    # such means that these have already been added so we don't get any
    # reports.
    # assert "Created User: 'nobody'" in err
    # assert "Created Directory: '/projects/'" in err
    # assert "Created Permission:" in err
    # assert "Created PermissionSet:" in err
    # assert "Created Language:" in err


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_initdb(capfd, po_directory, no_permission_sets, no_permissions,
                    no_users, no_projects, templates):
    """Initialise the database with initdb
    """
    templates.delete()
    call_command('initdb')
    out, err = capfd.readouterr()
    assert "Successfully populated the database." in out
    assert "pootle createsuperuser" in out
    assert (
        sorted(Project.objects.values_list("code", flat=True))
        == ["terminology", "tutorial"])
    po = Format.objects.get(name="po")
    # TODO: add unit tests for initdb
    assert po in Project.objects.get(code="terminology").filetypes.all()
    assert po in Project.objects.get(code="tutorial").filetypes.all()

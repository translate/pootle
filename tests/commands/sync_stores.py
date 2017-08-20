# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.management import call_command

from pootle_project.models import Project


@pytest.mark.cmd
@pytest.mark.django_db
def test_sync_stores_noargs(capfd, tmpdir):
    """Site wide sync_stores"""
    for project in Project.objects.all():
        fs_url = tmpdir.mkdir(project.code)
        project.config["pootle_fs.fs_url"] = str(fs_url)
    capfd.readouterr()
    call_command('sync_stores')
    out, err = capfd.readouterr()
    # FIXME we should work out how to get something here
    assert out == ''
    assert err == ''

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

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


@pytest.mark.cmd
@pytest.mark.django_db
def test_sync_stores_warn_on_conflict(caplog, project0, language0,
                                      tmpdir, settings):
    """Check warning if there are conflicting store/files"""
    settings.POOTLE_FS_WORKING_PATH = str(tmpdir.mkdir("__fs_tmp__"))
    fs_tmp = tmpdir.mkdir(project0.code)
    project0.config["pootle_fs.fs_url"] = str(fs_tmp)
    tp_tmp = fs_tmp.mkdir(language0.code)
    conflict_po = os.path.join(str(tp_tmp), "complex.po")
    with open(conflict_po, "w") as f:
        f.write("this file should conflict with complex.po in db")

    # the above code will create a conflict, if env changes this
    # test will need to be updated
    call_command('sync_stores', "--project=%s" % project0.code)
    rec = caplog.records[-1]
    assert rec.levelname == "WARNING"
    assert "tell pootle how to merge" in rec.message

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_format.models import Format


@pytest.mark.django_db
def test_fs_filetypes_changed_receiver(project_fs, project1, po2):

    project1.filetype_tool.add_filetype(po2)
    assert not project1.revisions.filter(key="pootle.fs.sync").count()
    project1.treestyle = "pootle_fs"
    project1.save()

    xliff = Format.objects.get(name="xliff")
    project1.filetypes.add(xliff)
    # still not configured
    assert not project1.revisions.filter(key="pootle.fs.sync").count()

    sync_start = project_fs.project.revisions.filter(
        key="pootle.fs.sync").first()
    project_fs.project.filetype_tool.add_filetype(po2)
    assert (
        sync_start
        != project_fs.project.revisions.filter(
            key="pootle.fs.sync").first())

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_app.project_tree import match_template_filename
from pootle_format.models import Format
from pootle_project.models import Project


@pytest.mark.django_db
def test_match_template_filename():
    project = Project.objects.get(code="project0")
    po = Format.objects.get(name="po")
    xliff = Format.objects.get(name="xliff")
    ts = Format.objects.get(name="ts")
    project.filetypes.add(xliff)
    project.filetypes.add(po)
    project.filetypes.add(ts)

    assert not match_template_filename(project, "foo.po")
    assert not match_template_filename(project, "foo.ts")
    assert not match_template_filename(project, "foo.xliff")
    assert match_template_filename(project, "foo.pot")

    assert not match_template_filename(project, "foo.p")
    assert not match_template_filename(project, "foo.pots")
    assert not match_template_filename(project, "foo.DOES_NOT_EXIST")

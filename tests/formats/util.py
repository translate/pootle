# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.delegate import formats
from pootle_format.exceptions import UnrecognizedFiletype
from pootle_format.models import Format
from pootle_project.models import Project


@pytest.mark.django_db
def test_format_util():

    project = Project.objects.get(code="project0")
    filetype_tool = project.filetype_tool
    assert list(filetype_tool.filetypes.all()) == list(project.filetypes.all())

    assert filetype_tool.filetype_extensions == ["po"]
    assert filetype_tool.template_extensions == ["pot"]
    assert filetype_tool.valid_extensions == ["po", "pot"]

    xliff = Format.objects.get(name="xliff")
    project.filetypes.add(xliff)
    assert filetype_tool.filetype_extensions == ["po", "xliff"]
    assert filetype_tool.template_extensions == ["pot", "xliff"]
    assert filetype_tool.valid_extensions == ["po", "xliff", "pot"]


@pytest.mark.django_db
def test_format_chooser():
    project = Project.objects.get(code="project0")
    registry = formats.get()
    po = Format.objects.get(name="po")
    po2 = registry.register("special_po_2", "po")
    po3 = registry.register("special_po_3", "po")
    xliff = Format.objects.get(name="xliff")
    project.filetypes.add(xliff)
    project.filetypes.add(po2)
    project.filetypes.add(po3)
    filetype_tool = project.filetype_tool

    assert filetype_tool.choose_filetype("foo.po") == po
    assert filetype_tool.choose_filetype("foo.pot") == po
    assert filetype_tool.choose_filetype("foo.xliff") == xliff

    # push po to the back of the queue
    project.filetypes.remove(po)
    project.filetypes.add(po)
    assert filetype_tool.choose_filetype("foo.po") == po2
    assert filetype_tool.choose_filetype("foo.pot") == po
    assert filetype_tool.choose_filetype("foo.xliff") == xliff

    with pytest.raises(UnrecognizedFiletype):
        filetype_tool.choose_filetype("foo.bar")

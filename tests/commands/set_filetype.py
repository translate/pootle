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

from pootle_project.models import Project


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_set_project_filetype(dummy_project_filetypes,
                                  templates_project0, po, po2):
    template_tp = templates_project0
    project = template_tp.project
    other_tps = project.translationproject_set.exclude(pk=template_tp.pk)
    result = project.filetype_tool.result

    project.filetype_tool.add_filetype(po2)
    call_command("set_filetype", "--project=project0", "special_po_2")

    assert result[0] == (template_tp, po2, None, None)
    for i, tp in enumerate(other_tps):
        assert result[i + 1] == (tp, po2, None, None)

    # test getting from_filetype
    result.clear()
    call_command(
        "set_filetype",
        "--project=project0",
        "--from-filetype=po",
        "special_po_2")
    assert result[0] == (template_tp, po2, po, None)
    for i, tp in enumerate(other_tps):
        assert result[i + 1] == (tp, po2, po, None)

    # test getting match
    result.clear()
    call_command(
        "set_filetype",
        "--project=project0",
        "--matching=bar",
        "special_po_2")
    assert result[0] == (template_tp, po2, None, "bar")
    for i, tp in enumerate(other_tps):
        assert result[i + 1] == (tp, po2, None, "bar")

    # test getting both
    result.clear()
    call_command(
        "set_filetype",
        "--project=project0",
        "--from-filetype=po",
        "--matching=bar",
        "special_po_2")
    assert result[0] == (template_tp, po2, po, "bar")
    for i, tp in enumerate(other_tps):
        assert result[i + 1] == (tp, po2, po, "bar")


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_set_all_project_filetypes(dummy_project_filetypes, templates, po2):

    for project in Project.objects.all():
        project.filetype_tool.add_filetype(po2)

    # grab the result object from a project
    result = project.filetype_tool.result

    call_command("set_filetype", "special_po_2")
    i = 0
    for project in Project.objects.all():
        project_tps = project.translationproject_set.all()
        for tp in project.translationproject_set.all():
            if tp.is_template_project:
                assert result[i] == (tp, po2, None, None)
                i += 1
                project_tps = project_tps.exclude(pk=tp.pk)
        for tp in project_tps:
            assert result[i] == (tp, po2, None, None)
            i += 1


@pytest.mark.cmd
@pytest.mark.django_db
def test_cmd_set_project_filetypes_bad():
    with pytest.raises(CommandError):
        call_command(
            "set_filetype",
            "--project=project0",
            "--from-filetype=FORMAT_DOES_NOT_EXIST",
            "po")
    with pytest.raises(CommandError):
        call_command(
            "set_filetype",
            "--project=project0",
            "FORMAT_DOES_NOT_EXIST")

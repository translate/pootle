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
from pootle_store.models import PARSED, Store


@pytest.mark.cmd
@pytest.mark.django_db
def test_sync_stores_noargs(capfd, en_tutorial_po_member_updated):
    """Site wide sync_stores"""
    call_command('sync_stores')
    out, err = capfd.readouterr()
    # FIXME we should work out how to get something here
    assert out == ''
    assert err == ''


@pytest.mark.cmd
@pytest.mark.django_db
def test_sync_stores_project_tree_none(capfd):
    project = Project.objects.get(code="project0")
    store = Store.objects.live().filter(
        translation_project__project=project).first()
    store.file = store.name
    store.state = PARSED
    store.save()
    project.treestyle = "none"
    project.save()
    capfd.readouterr()
    call_command("sync_stores", "--project", project.code, "--force", "--overwrite")
    out, err = capfd.readouterr()
    # wierdly this normally logs to stderr
    assert not err

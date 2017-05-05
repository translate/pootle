# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest


@pytest.fixture
def project_fs(tmpdir, settings):
    from pootle_project.models import Project
    from pootle_fs.utils import FSPlugin

    project = Project.objects.get(code="project0")
    new_url = os.path.join(str(tmpdir), "__src__")
    project.config["pootle_fs.fs_url"] = new_url
    plugin = FSPlugin(project)
    os.makedirs(new_url)
    settings.POOTLE_FS_WORKING_PATH = str(tmpdir)
    plugin.fetch()
    return plugin


@pytest.fixture
def project_fs_empty(english, tmpdir, settings):
    from pytest_pootle.factories import ProjectDBFactory

    from pootle_fs.utils import FSPlugin

    project = ProjectDBFactory(
        source_language=english,
        code="project_fs_empty",
        treestyle='pootle_fs')
    settings.POOTLE_FS_WORKING_PATH = str(tmpdir)
    repo_path = os.path.join(str(tmpdir), "__src__")
    if not os.path.exists(repo_path):
        os.mkdir(repo_path)
    project.config["pootle_fs.fs_type"] = "localfs"
    project.config["pootle_fs.fs_url"] = repo_path
    project.config["pootle_fs.translation_mappings"] = {
        "default": "/<language_code>/<dir_path>/<filename>.<ext>"}
    return FSPlugin(project)

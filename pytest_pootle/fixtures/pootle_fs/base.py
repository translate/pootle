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

    from pootle.core.delegate import config
    from pootle_fs.utils import FSPlugin
    from pootle_project.models import Project

    project = ProjectDBFactory(
        source_language=english,
        code="project_fs_empty",
        treestyle='pootle_fs')
    settings.POOTLE_FS_WORKING_PATH = str(tmpdir)
    repo_path = os.path.join(str(tmpdir), "__src__")
    if not os.path.exists(repo_path):
        os.mkdir(repo_path)
    conf = config.get(Project, instance=project)
    conf.set_config("pootle_fs.fs_type", "localfs")
    conf.set_config("pootle_fs.fs_url", repo_path)
    conf.set_config(
        "pootle_fs.translation_mappings",
        {"default": "/<language_code>/<dir_path>/<filename>.<ext>"})
    return FSPlugin(project)


@pytest.fixture
def no_fs_files(request):
    from pootle_fs.delegate import fs_file

    file_receivers = fs_file.receivers
    fs_file.receivers = []

    def reconnect():
        fs_file.receivers = file_receivers
    request.addfinalizer(reconnect)


@pytest.fixture
def no_fs_plugins(request):
    from pootle_fs.delegate import fs_plugins

    plugins_receivers = fs_plugins.receivers
    fs_plugins.receivers = []

    def reconnect():
        fs_plugins.receivers = plugins_receivers
    request.addfinalizer(reconnect)


@pytest.fixture
def no_fs_finder(request):
    from pootle_fs.delegate import fs_finder

    finder_receivers = fs_finder.receivers
    fs_finder.receivers = []

    def reconnect():
        fs_finder.receivers = finder_receivers
    request.addfinalizer(reconnect)

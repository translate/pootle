# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil

import pytest


def _require_project(code, name, source_language, **kwargs):
    """Helper to get/create a new project."""
    from pootle_project.models import Project

    criteria = {
        'code': code,
        'fullname': name,
        'source_language': source_language,
        'checkstyle': 'standard',
        'treestyle': 'auto',
    }
    criteria.update(kwargs)
    new_project = Project.objects.get_or_create(**criteria)[0]
    return new_project


@pytest.fixture
def tutorial(english, settings):
    """Require `tutorial` test project."""
    import pytest_pootle

    shutil.copytree(
        os.path.join(
            os.path.dirname(pytest_pootle.__file__),
            "data", "po", "tutorial"),
        os.path.join(
            settings.POOTLE_TRANSLATION_DIRECTORY,
            "tutorial"))

    return _require_project('tutorial', 'Tutorial', english)


@pytest.fixture
def tutorial_disabled(english):
    """Require `tutorial-disabled` test project in a disabled state."""
    return _require_project('tutorial-disabled', 'Tutorial', english,
                            disabled=True)


@pytest.fixture
def project_foo(english, request):
    """Require `foo` test project."""
    foo = _require_project('foo', 'Foo Project', english)

    def _remove_dir():
        foo_path = foo.get_real_path()
        if os.path.exists(foo_path):
            shutil.rmtree(foo_path)
    request.addfinalizer(_remove_dir)

    return foo


@pytest.fixture
def project_bar(english, request):
    """Require `bar` test project."""
    bar = _require_project('bar', 'Bar Project', english)

    def _remove_dir():
        bar_path = bar.get_real_path()
        if os.path.exists(bar_path):
            shutil.rmtree(bar_path)

    request.addfinalizer(_remove_dir)

    return bar


@pytest.fixture
def project0():
    """project0 Project"""
    from pootle_project.models import Project

    return Project.objects.get(code="project0")


@pytest.fixture
def project1():
    """project0 Project"""
    from pootle_project.models import Project

    return Project.objects.get(code="project1")


@pytest.fixture
def project0_directory(po_directory, project0):
    """project0 Project"""
    return project0


@pytest.fixture
def project0_nongnu(project0_directory, project0, settings):
    project0.treestyle = "nongnu"
    project0.save()
    project_dir = os.path.join(
        settings.POOTLE_TRANSLATION_DIRECTORY, project0.code)
    if not os.path.exists(project_dir):
        os.makedirs(project_dir)
    for tp in project0.translationproject_set.all():
        tp.save()
    return project0


@pytest.fixture
def project_dir_resources0(project0, subdir0):
    """Returns a ProjectResource object for a Directory"""

    from pootle_app.models import Directory
    from pootle_project.models import ProjectResource

    resources = Directory.objects.live().filter(
        name=subdir0.name,
        parent__translationproject__project=project0)
    return ProjectResource(
        resources,
        ("/projects/%s/%s"
         % (project0.code,
            subdir0.name)))


@pytest.fixture
def project_store_resources0(project0, subdir0):
    """Returns a ProjectResource object for a Store"""

    from pootle_project.models import ProjectResource
    from pootle_store.models import Store

    store = subdir0.child_stores.live().first()
    resources = Store.objects.live().filter(
        name=store.name,
        parent__name=subdir0.name,
        translation_project__project=project0)

    return ProjectResource(
        resources,
        ("/projects/%s/%s/%s"
         % (project0.code,
            subdir0.name,
            store.name)))


@pytest.fixture
def project_set():
    from pootle_project.models import Project, ProjectSet

    return ProjectSet(Project.objects.exclude(disabled=True))

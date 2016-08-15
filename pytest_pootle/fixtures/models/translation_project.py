# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import shutil

import pytest

from pootle.core.delegate import tp_tool


def pytest_generate_tests(metafunc):
    from pootle_project.models import PROJECT_CHECKERS

    if 'checkers' in metafunc.funcargnames:
        metafunc.parametrize("checkers", PROJECT_CHECKERS.keys())


def _require_tp(language, project):
    """Helper to get/create a new translation project."""
    from pootle_translationproject.models import create_translation_project

    return create_translation_project(language, project)


def _require_tp_with_obsolete_dir(language, project):
    """Helper to get/create a translation project in obsolete state."""
    from pootle_translationproject.models import create_translation_project

    tp = create_translation_project(language, project)
    tp.directory.makeobsolete()

    return tp


@pytest.fixture
def afrikaans_tutorial(afrikaans, tutorial):
    """Require Afrikaans Tutorial."""
    return _require_tp(afrikaans, tutorial)


@pytest.fixture
def arabic_tutorial_obsolete(arabic, tutorial):
    """Require Arabic Tutorial in obsolete state."""
    return _require_tp_with_obsolete_dir(arabic, tutorial)


@pytest.fixture
def english_tutorial(english, tutorial):
    """Require English Tutorial."""
    return _require_tp(english, tutorial)


@pytest.fixture
def french_tutorial(french, tutorial):
    """Require French Tutorial."""
    return _require_tp(french, tutorial)


@pytest.fixture
def spanish_tutorial(spanish, tutorial):
    """Require Spanish Tutorial."""
    return _require_tp(spanish, tutorial)


@pytest.fixture
def italian_tutorial(italian, tutorial):
    """Require Italian Tutorial."""
    return _require_tp(italian, tutorial)


@pytest.fixture
def russian_tutorial(russian, tutorial):
    """Require Russian Tutorial."""
    return _require_tp(russian, tutorial)


@pytest.fixture
def afrikaans_vfolder_test(afrikaans, vfolder_project):
    """Require Afrikaans Virtual Folder Test."""
    return _require_tp(afrikaans, vfolder_project)


@pytest.fixture
def tp_checker_tests(request, english, checkers):
    from pytest_pootle.factories import ProjectDBFactory

    checker_name = checkers
    project = ProjectDBFactory(
        checkstyle=checker_name,
        source_language=english)

    def _remove_project_directory():
        shutil.rmtree(project.get_real_path())
    request.addfinalizer(_remove_project_directory)

    return (checker_name, project)


@pytest.fixture
def templates_project0(request, templates, project0):
    """Require the templates/project0/ translation project."""
    from pytest_pootle.factories import TranslationProjectFactory

    tp = TranslationProjectFactory(language=templates, project=project0)

    def _cleanup():
        shutil.rmtree(tp.abs_real_path)

    request.addfinalizer(_cleanup)

    return tp


@pytest.fixture
def tp0(language0, project0):
    """Require English Project0."""
    from pootle_translationproject.models import TranslationProject

    return TranslationProject.objects.get(
        language=language0,
        project=project0)


@pytest.fixture
def no_tp_tool_(request):
    start_receivers = tp_tool.receivers
    tp_tool.receivers = []

    def _reset_tp_tool():
        tp_tool.receivers = start_receivers

    request.addfinalizer(_reset_tp_tool)

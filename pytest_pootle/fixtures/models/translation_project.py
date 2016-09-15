# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

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


@pytest.fixture
def afrikaans_tutorial(afrikaans, tutorial):
    """Require Afrikaans Tutorial."""
    return _require_tp(afrikaans, tutorial)


@pytest.fixture
def en_tutorial_obsolete(english_tutorial):
    """Require Arabic Tutorial in obsolete state."""
    english_tutorial.directory.makeobsolete()
    return english_tutorial


@pytest.fixture
def english_tutorial(english, tutorial):
    """Require English Tutorial."""
    return _require_tp(english, tutorial)


@pytest.fixture
def italian_tutorial(italian, tutorial):
    """Require Italian Tutorial."""
    return _require_tp(italian, tutorial)


@pytest.fixture
def tp_checker_tests(request, english, checkers):
    from pytest_pootle.factories import ProjectDBFactory

    checker_name = checkers
    project = ProjectDBFactory(
        checkstyle=checker_name,
        source_language=english)
    return (checker_name, project)


@pytest.fixture
def templates_project0(request, templates, project0):
    """Require the templates/project0/ translation project."""
    from pytest_pootle.factories import TranslationProjectFactory

    return TranslationProjectFactory(language=templates, project=project0)


@pytest.fixture
def tp0(language0, project0):
    """Require English Project0."""
    from pootle_translationproject.models import TranslationProject

    return TranslationProject.objects.get(
        language=language0,
        project=project0)


@pytest.fixture
def tp1(language1, project1):
    """Returns the tp created by language1 and project1 fixtures."""
    from pootle_translationproject.models import TranslationProject

    return TranslationProject.objects.get(
        language=language1,
        project=project1)


@pytest.fixture
def no_tp_tool_(request):
    start_receivers = tp_tool.receivers
    tp_tool.receivers = []

    def _reset_tp_tool():
        tp_tool.receivers = start_receivers

    request.addfinalizer(_reset_tp_tool)

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest
from translate.storage.factory import getclass


def pytest_generate_tests(metafunc):
    import pytest_pootle

    if 'terminology_units' in metafunc.fixturenames:
        term_file = os.path.join(
            os.path.dirname(pytest_pootle.__file__),
            *("data", "po", "terminology.po"))
        with open(term_file) as f:
            _terms = [x.source for x in getclass(f)(f.read()).units[1:]]
        metafunc.parametrize("terminology_units", _terms)


@pytest.fixture
def terminology_project():
    from pootle_project.models import Project

    return Project.objects.get(code="terminology")


@pytest.fixture
def terminology0(language0, terminology_project):
    from pootle_translationproject.models import TranslationProject

    return TranslationProject.objects.get(
        language=language0,
        project__code="terminology")

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import pytest

from django.http import Http404

from pootle.core.decorators import get_path_obj
from pootle_language.models import Language
from pootle_project.models import Project
from pootle_translationproject.models import TranslationProject


@pytest.mark.django_db
def test_get_path_obj(rf, default, afrikaans_tutorial,
                      arabic_tutorial_disabled, tutorial_disabled):
    """Ensure the correct path object is retrieved."""
    language_code = afrikaans_tutorial.language.code
    project_code = afrikaans_tutorial.project.code

    project_code_disabled = tutorial_disabled.code

    language_code_fake = 'faf'
    project_code_fake = 'fake-tutorial'

    request = rf.get('/')
    request.user = default

    # Fake decorated function
    func = get_path_obj(lambda x, y: (x, y))

    # Single project
    func(request, project_code=project_code)
    assert isinstance(request.ctx_obj, Project)

    # Missing/disabled project
    with pytest.raises(Http404):
        func(request, project_code=project_code_fake)

    with pytest.raises(Http404):
        func(request, project_code=project_code_disabled)

    # Single language
    func(request, language_code=language_code)
    assert isinstance(request.ctx_obj, Language)

    # Missing language
    with pytest.raises(Http404):
        func(request, language_code=language_code_fake)

    # Translation Project
    func(request, language_code=language_code, project_code=project_code)
    assert isinstance(request.ctx_obj, TranslationProject)

    # Missing/disabled Translation Project
    with pytest.raises(Http404):
        func(request, language_code=language_code_fake,
             project_code=project_code)

    with pytest.raises(Http404):
        func(request, language_code=language_code,
             project_code=project_code_disabled)

    with pytest.raises(Http404):
        func(request, language_code=arabic_tutorial_disabled.language.code,
             project_code=arabic_tutorial_disabled.project.code)

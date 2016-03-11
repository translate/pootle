# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_app.forms import ProjectForm
from pootle_project.models import (PROJECT_CHECKERS, RESERVED_PROJECT_CODES,
                                   Project)
from pootle_store.filetypes import filetype_choices


@pytest.mark.parametrize('reserved_code', RESERVED_PROJECT_CODES)
@pytest.mark.django_db
def test_clean_code_invalid(reserved_code):
    form_data = {
        'code': reserved_code,
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'localfiletype': filetype_choices[0][0],
        'source_language': 1,
        'treestyle': Project.treestyle_choices[0][0],
    }
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'code' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_clean_localfiletype_invalid():
    form_data = {
        'code': 'foo',
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'localfiletype': 'invalid_filetype',
        'source_language': 1,
        'treestyle': Project.treestyle_choices[0][0],
    }
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'localfiletype' in form.errors
    assert len(form.errors.keys()) == 1

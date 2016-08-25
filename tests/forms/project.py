# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle_app.forms import ProjectForm
from pootle_format.models import Format
from pootle_project.models import (PROJECT_CHECKERS, RESERVED_PROJECT_CODES,
                                   Project)


@pytest.mark.parametrize('reserved_code', RESERVED_PROJECT_CODES)
@pytest.mark.django_db
def test_clean_code_invalid(reserved_code, format_registry):
    form_data = {
        'code': reserved_code,
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'filetypes': [format_registry["po"]["pk"]],
        'source_language': 1,
        'treestyle': Project.treestyle_choices[0][0],
    }
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'code' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_clean_code_blank_invalid(format_registry):
    form_data = {
        'code': '  ',
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'filetypes': [format_registry["po"]["pk"]],
        'source_language': 1,
        'treestyle': Project.treestyle_choices[0][0],
    }
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'code' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_clean_localfiletype_invalid(format_registry):
    form_data = {
        'code': 'foo',
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'fullname': 'Foo',
        'filetypes': ["NO_SUCH_FORMAT"],
        'source_language': 1,
        'treestyle': Project.treestyle_choices[0][0],
    }
    form = ProjectForm(form_data)
    assert not form.is_valid()
    assert 'filetypes' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_project_form_bad_filetype_removal(format_registry):
    form_data = {
        'fullname': "Project 0",
        'code': "project0",
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'disabled': False,
        'filetypes': [Format.objects.get(name="xliff").pk],
        'source_language': 1,
        'screenshot_search_prefix': "",
        'ignoredfiles': "",
        'report_email': "",
        'treestyle': Project.treestyle_choices[0][0],
    }
    form = ProjectForm(form_data, instance=Project.objects.get(code="project0"))
    assert not form.is_valid()
    assert 'filetypes' in form.errors
    assert len(form.errors.keys()) == 1


@pytest.mark.django_db
def test_project_form_change_filetypes(format_registry):
    filetype_names = ["xliff", "po", "ts"]
    filetypes = []
    for filetype in filetype_names:
        filetypes.append(Format.objects.get(name=filetype).pk)
    form_data = {
        'fullname': "Project 0",
        'code': "project0",
        'checkstyle': PROJECT_CHECKERS.keys()[0],
        'disabled': False,
        'filetypes': filetypes,
        'source_language': 1,
        'screenshot_search_prefix': "",
        'ignoredfiles': "",
        'report_email': "",
        'treestyle': Project.treestyle_choices[0][0],
    }
    project0 = Project.objects.get(code="project0")
    form = ProjectForm(form_data, instance=project0)
    assert form.is_valid()
    form.save()
    assert (
        list(project0.filetypes.values_list("pk", flat=True))
        == filetypes)

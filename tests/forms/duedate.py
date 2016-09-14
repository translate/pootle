# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.utils import timezone

from pytest_pootle.factories import UserFactory

from duedates.forms import DueDateForm
from duedates.models import INVALID_POOTLE_PATHS


@pytest.mark.parametrize('pootle_path', INVALID_POOTLE_PATHS)
def test_duedate_form_validation_invalid_paths(pootle_path):
    """Tests certain path restrictions when validating due date forms."""
    form_data = {
        'pootle_path': pootle_path,
    }
    form = DueDateForm(form_data)
    assert not form.is_valid()

    assert 'pootle_path' in form.errors
    assert 'Cannot set due date for this path.' in form.errors['pootle_path']


@pytest.mark.django_db
@pytest.mark.parametrize('due_on', [timezone.now(), '2016-09-06T14:19:52.985Z'])
@pytest.mark.parametrize('pootle_path', [
    '/ru/', '/ru/foo/', '/ru/foo/bar/', '/ru/foo/bar/baz.po',
    '/projects/foo/', '/projects/foo/bar/', '/projects/foo/bar/baz.po'
])
def test_duedate_create(due_on, pootle_path):
    """Tests form validation for a set of paths and date time formats."""
    user = UserFactory.create()

    form_data = {
        'due_on': due_on,
        'modified_by': user.id,
        'pootle_path': pootle_path,
    }
    form = DueDateForm(form_data)
    assert form.is_valid()
    due_date = form.save()
    assert due_date.id is not None

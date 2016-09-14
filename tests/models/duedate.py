# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.core.exceptions import ValidationError
from django.utils import timezone

from pytest_pootle.factories import UserFactory

from duedates.models import INVALID_POOTLE_PATHS, DueDate


@pytest.mark.django_db
@pytest.mark.parametrize('pootle_path', INVALID_POOTLE_PATHS)
def test_duedate_create_invalid_paths(pootle_path):
    """Tests certain path restrictions when creating due dates."""
    with pytest.raises(ValidationError) as excinfo:
        DueDate.objects.create(pootle_path=pootle_path)

    message_dict = excinfo.value.message_dict
    assert 'pootle_path' in message_dict
    assert 'Cannot set due date for this path.' in message_dict['pootle_path']


@pytest.mark.django_db
@pytest.mark.parametrize('pootle_path', [
    '/ru/', '/ru/foo/', '/ru/foo/bar/', '/ru/foo/bar/baz.po',
    '/projects/foo/', '/projects/foo/bar/', '/projects/foo/bar/baz.po'
])
def test_duedate_create(pootle_path):
    """Tests due dates creation for valid paths."""
    user = UserFactory.create()
    due_on = timezone.now()

    due_date = DueDate.objects.create(
        due_on=due_on,
        modified_by=user,
        pootle_path=pootle_path,
    )
    assert due_date.id is not None

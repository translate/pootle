# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from django.db import connection
from django.utils import timezone

from pytest_pootle.factories import DueDateFactory, UserFactory
from pytest_pootle.utils import create_api_request

from pootle.core.utils.json import jsonify

from duedates.models import DueDate
from duedates.api import DueDateView


def test_duedate_get(rf):
    """Tests the due date endpoint cannot be GET'ed."""
    view = DueDateView.as_view()
    request = create_api_request(rf, url='/')
    response = view(request)
    assert response.status_code == 405


@pytest.mark.django_db
def test_duedate_post(rf):
    """Tests due dates can be added."""
    view = DueDateView.as_view()
    user = UserFactory.create()
    due_on = timezone.now()
    pootle_path = '/ru/foo/bar/'

    request_data = {
        'due_on': due_on,
        'modified_by': user.id,
        'pootle_path': pootle_path,
    }
    request = create_api_request(rf, method='POST', data=request_data)
    response = view(request)
    assert response.status_code == 200

    due_date = DueDate.objects.latest('id')

    # MySQL < 5.6.4 doesn't support microsecond precision
    if not connection.features.supports_microsecond_precision:
        due_on = due_on.replace(microsecond=0)

    # Not checking `datetime` objects directly because microseconds are adjusted
    # when serializing, so checking the serialized values.
    assert jsonify(due_date.due_on) == jsonify(due_on)
    assert due_date.modified_by == user
    assert due_date.pootle_path == pootle_path


@pytest.mark.django_db
def test_duedate_delete(rf):
    """Tests due dates can be deleted."""
    view = DueDateView.as_view()
    user = UserFactory.create()
    due_on = timezone.now()
    pootle_path = '/ru/foo/bar/'

    data = {
        'due_on': due_on,
        'modified_by': user,
        'pootle_path': pootle_path,
    }
    due_date = DueDateFactory.create(**data)

    assert due_date.id is not None
    due_date_count_pre_delete = DueDate.objects.count()

    request = create_api_request(rf, method='DELETE')
    view_kwargs = {
        'id': due_date.id,
    }
    response = view(request, **view_kwargs)
    assert response.status_code == 200
    assert DueDate.objects.count() == due_date_count_pre_delete - 1

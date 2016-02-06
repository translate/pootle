# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pytest_pootle.env import PootleTestEnv


@pytest.fixture(autouse=True, scope='session')
def post_db_setup(_django_db_setup, _django_cursor_wrapper, request):
    with _django_cursor_wrapper:
        PootleTestEnv(request).setup()


@pytest.fixture
def no_projects():
    from pootle_project.models import Project

    Project.objects.all().delete()


@pytest.fixture
def no_permissions():
    from django.contrib.auth.models import Permission

    Permission.objects.all().delete()


@pytest.fixture
def no_permission_sets():
    from pootle_app.models import PermissionSet

    PermissionSet.objects.all().delete()


@pytest.fixture
def no_submissions():
    from pootle_statistics.models import Submission

    Submission.objects.all().delete()


@pytest.fixture
def no_users():
    from django.contrib.auth import get_user_model

    User = get_user_model()
    User.objects.all().delete()


@pytest.fixture
def no_extra_users():
    from django.contrib.auth import get_user_model

    User = get_user_model()
    User.objects.exclude(
        username__in=["system", "default", "nobody"]).delete()

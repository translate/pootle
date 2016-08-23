# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import tempfile

import pytest

from pytest_pootle.env import PootleTestEnv



@pytest.fixture(autouse=True, scope='session')
def setup_db_if_needed(request):
    """Sets up the site DB only if tests requested to use the DB (autouse)."""
    is_db_marker_set = [
        item for item in request.node.items
        if item.get_marker('django_db')
    ]
    if is_db_marker_set:
        return request.getfuncargvalue('post_db_setup')


@pytest.fixture(scope='session')
def post_db_setup(translations_directory, _django_db_setup,
                  _django_cursor_wrapper, request):
    """Sets up the site DB for the test session."""
    with _django_cursor_wrapper:
        PootleTestEnv(request).setup()


@pytest.fixture
def no_projects():
    from pootle_project.models import Project

    Project.objects.all().delete()


@pytest.fixture
def no_vfolders():
    from virtualfolder.models import VirtualFolder

    VirtualFolder.objects.all().delete()


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


@pytest.fixture(autouse=True, scope="session")
def translations_directory():
    """used by PootleEnv"""
    from django.conf import settings

    settings.POOTLE_TRANSLATION_DIRECTORY = tempfile.mkdtemp()


@pytest.fixture(autouse=True)
def clear_cache():
    """Currently tests only use one cache so this clears all"""

    from django.core.cache import caches

    from django_redis import get_redis_connection

    get_redis_connection('default').flushdb()
    caches["exports"].clear()


@pytest.fixture(scope="session")
def test_fs():
    """A convenience fixture for retrieving data from test files"""
    import pytest_pootle

    class TestFs(object):

        def path(self, path):
            return os.path.join(
                os.path.dirname(pytest_pootle.__file__),
                path)

        def open(self, paths, *args, **kwargs):
            if isinstance(paths, (list, tuple)):
                paths = os.path.join(*paths)
            return open(self.path(paths), *args, **kwargs)

    return TestFs()

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools
import os
import shutil
import tempfile
import time

import pytest

from pytest_pootle.env import PootleTestEnv


@pytest.fixture(autouse=True)
def test_timing(request, settings, log_timings):
    from django.db import reset_queries

    if not request.config.getoption("--debug-tests"):
        return
    settings.DEBUG = True
    reset_queries()
    start = time.time()
    request.addfinalizer(
        functools.partial(
            log_timings,
            request.node.name,
            start))


@pytest.fixture
def po_test_dir(request, tmpdir):
    po_dir = str(tmpdir.mkdir("po"))

    def rm_po_dir():
        if os.path.exists(po_dir):
            shutil.rmtree(po_dir)

    request.addfinalizer(rm_po_dir)
    return po_dir


@pytest.fixture
def po_directory(request, po_test_dir, settings):
    """Sets up a tmp directory for PO files."""
    from pootle_store.models import fs

    translation_directory = settings.POOTLE_TRANSLATION_DIRECTORY

    # Adjust locations
    settings.POOTLE_TRANSLATION_DIRECTORY = po_test_dir
    fs.location = po_test_dir

    def _cleanup():
        settings.POOTLE_TRANSLATION_DIRECTORY = translation_directory

    request.addfinalizer(_cleanup)


@pytest.fixture(scope='session')
def tests_use_db(request):
    return bool(
        [item for item in request.node.items
         if item.get_marker('django_db')])


@pytest.fixture(scope='session')
def tests_use_vfolders(request):
    return bool(
        [item for item in request.node.items
         if item.get_marker('pootle_vfolders')])


@pytest.fixture(scope='session')
def tests_use_migration(request, tests_use_db):
    return bool(
        tests_use_db
        and [item for item in request.node.items
             if item.get_marker('django_migration')])


@pytest.fixture(autouse=True, scope='session')
def setup_db_if_needed(request, tests_use_db):
    """Sets up the site DB only if tests requested to use the DB (autouse)."""
    if tests_use_db and not request.config.getvalue('reuse_db'):
        return request.getfuncargvalue('post_db_setup')


@pytest.fixture(scope='session')
def post_db_setup(translations_directory, django_db_setup, django_db_blocker,
                  tests_use_db, tests_use_vfolders, request):
    """Sets up the site DB for the test session."""
    if tests_use_db:
        with django_db_blocker.unblock():
            PootleTestEnv().setup(
                vfolders=tests_use_vfolders)


@pytest.fixture(scope='session')
def django_db_use_migrations(tests_use_migration):
    return tests_use_migration


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
def translations_directory(request):
    """used by PootleEnv"""
    from django.conf import settings

    settings.POOTLE_TRANSLATION_DIRECTORY = tempfile.mkdtemp()

    def rm_tmp_dir():
        shutil.rmtree(settings.POOTLE_TRANSLATION_DIRECTORY)

    request.addfinalizer(rm_tmp_dir)


@pytest.fixture
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

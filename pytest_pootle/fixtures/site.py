# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import functools
import inspect
import os
import pdb
import shutil
import sys
import tempfile
import time

import pytest
from pytest_pootle.env import PootleTestEnv

from pootle.core.debug import debug_sql


@pytest.fixture(autouse=True)
def test_timing(request, log_timings):
    from django.db import reset_queries

    if not request.config.getoption("--debug-tests"):
        return
    from django.conf import settings
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
    translation_directory = settings.POOTLE_TRANSLATION_DIRECTORY

    # Adjust locations
    settings.POOTLE_TRANSLATION_DIRECTORY = po_test_dir

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
    force_migration = request.config.getoption("--force-migration")
    return bool(
        force_migration
        or (tests_use_db
            and [item for item in request.node.items
                 if item.get_marker('django_migration')]))


@pytest.fixture(autouse=True, scope='session')
def debug_utils(request):

    class _TraceEvent(object):

        def __init__(self, *args, **kwargs):
            self.stack = inspect.stack()[2]
            self.args = args
            self.kwargs = kwargs

        def __str__(self):
            return ", ".join(
                [self.stack[1],
                 str(self.stack[2]),
                 self.stack[3],
                 str(self.args),
                 str(self.kwargs)])

    class _Trace(object):
        debug = False
        _called = ()

        def __call__(self, *args, **kwargs):
            self._called += (_TraceEvent(*args, **kwargs), )

        def __iter__(self):
            for event in self._called:
                yield event
            self._called = ()

        def __str__(self):
            return "\n".join(str(item) for item in self._called)

    sys.modules["__builtin__"].__dict__["_trace"] = _Trace()
    sys.modules["__builtin__"].__dict__["pdb"] = pdb
    sys.modules["__builtin__"].__dict__["debug_sql"] = debug_sql


@pytest.fixture(autouse=True, scope='session')
def setup_db_if_needed(request, tests_use_db):
    """Sets up the site DB only if tests requested to use the DB (autouse)."""
    if tests_use_db and not request.config.getvalue('reuse_db'):
        return request.getfixturevalue('post_db_setup')


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
def no_users(no_units):
    from django.contrib.auth import get_user_model

    User = get_user_model()
    User.objects.all().delete()


@pytest.fixture
def no_units():
    from pootle_store.models import Unit

    Unit.objects.all().delete()


@pytest.fixture
def no_templates_tps(templates):
    templates.translationproject_set.all().delete()


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
    get_redis_connection('lru').flushdb()
    get_redis_connection('redis').flushdb()
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


@pytest.fixture
def media_test_dir(request, settings, tmpdir):
    media_dir = str(tmpdir.mkdir("media"))
    settings.MEDIA_ROOT = media_dir

    def rm_media_dir():
        if os.path.exists(media_dir):
            shutil.rmtree(media_dir)

    request.addfinalizer(rm_media_dir)
    return media_dir


@pytest.fixture(scope="session")
def export_dir(request):
    export_dir = tempfile.mkdtemp()

    def rm_export_dir():
        if os.path.exists(export_dir):
            shutil.rmtree(export_dir)

    request.addfinalizer(rm_export_dir)

    return export_dir


@pytest.fixture
def cd_export_dir(request, export_dir):
    curdir = os.path.abspath(os.curdir)
    os.chdir(export_dir)

    def cd_curdir():
        os.chdir(curdir)

    request.addfinalizer(cd_curdir)

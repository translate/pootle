# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil
from pkgutil import iter_modules

import pytest

from . import fixtures
from .fixtures import models as fixtures_models
from .fixtures.core import management as fixtures_core_management
from .fixtures.core import utils as fixtures_core_utils
from .fixtures import formats as fixtures_formats
from .fixtures import pootle_fs as fixtures_fs


def _load_fixtures(*modules):
    for mod in modules:
        path = mod.__path__
        prefix = '%s.' % mod.__name__

        for loader_, name, is_pkg in iter_modules(path, prefix):
            if not is_pkg:
                yield name


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


pytest_plugins = tuple(
    _load_fixtures(
        fixtures,
        fixtures_core_management,
        fixtures_core_utils,
        fixtures_formats,
        fixtures_models,
        fixtures_fs))

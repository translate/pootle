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
from .fixtures.core import utils as fixtures_core_utils


def _load_fixtures(*modules):
    for mod in modules:
        path = mod.__path__
        prefix = '%s.' % mod.__name__

        for loader, name, is_pkg in iter_modules(path, prefix):
            if not is_pkg:
                yield name


# this must be here to be used in every test
@pytest.fixture(autouse=True)
def po_directory(request, tmpdir, settings):
    """Sets up a tmp directory for PO files."""
    from pootle_store.models import fs

    po_dir = str(tmpdir.mkdir("po"))

    projects = [
        dirname for dirname
        in os.listdir(settings.POOTLE_TRANSLATION_DIRECTORY)
        if dirname != '.tmp']

    for project in projects:
        src_dir = os.path.join(settings.POOTLE_TRANSLATION_DIRECTORY, project)

        # Copy files over the temporary dir
        shutil.copytree(src_dir, os.path.join(po_dir, project))

    # Adjust locations
    settings.POOTLE_TRANSLATION_DIRECTORY = po_dir
    fs.location = po_dir

    def _cleanup():
        for f in tmpdir.listdir():
            f.remove()
    request.addfinalizer(_cleanup)


pytest_plugins = tuple(
    _load_fixtures(fixtures, fixtures_core_utils, fixtures_models),
)

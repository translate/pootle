# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import shutil
from collections import OrderedDict

import pytest

from .models import store


FILE_IMPORT_FAIL_TESTS = OrderedDict()
FILE_IMPORT_FAIL_TESTS["revision_header_missing.po"] = "MissingPootleRevError"
FILE_IMPORT_FAIL_TESTS["revision_header_invalid.po"] = "MissingPootleRevError"
FILE_IMPORT_FAIL_TESTS["path_header_missing.po"] = "MissingPootlePathError"
FILE_IMPORT_FAIL_TESTS["path_header_invalid.po"] = "FileImportError"


@pytest.fixture
def file_import_failure(file_import_failure_names):
    from import_export import exceptions

    return (
        file_import_failure_names,
        getattr(
            exceptions, FILE_IMPORT_FAIL_TESTS[file_import_failure_names]))


@pytest.fixture
def ts_directory(request, tmpdir):
    """Sets up a tmp directory with test ts files."""

    from django.conf import settings
    from pootle_store.models import fs

    test_base_dir = str(tmpdir)

    ts_translation_dir = os.path.join(settings.ROOT_DIR,
                                      'tests', 'data', 'ts')

    projects = [dirname for dirname
                in os.listdir(ts_translation_dir)
                if dirname != '.tmp']
    for project in projects:
        src_dir = os.path.join(ts_translation_dir, project)

        # Copy files over the temporal dir
        shutil.copytree(src_dir, os.path.join(test_base_dir, project))

    pootle_dir = settings.POOTLE_TRANSLATION_DIRECTORY

    # Adjust locations
    settings.POOTLE_TRANSLATION_DIRECTORY = test_base_dir
    fs.location = test_base_dir

    def _cleanup():
        shutil.rmtree(test_base_dir)
        settings.POOTLE_TRANSLATION_DIRECTORY = pootle_dir
        fs.location = pootle_dir

    request.addfinalizer(_cleanup)

    return test_base_dir


@pytest.fixture
def en_tutorial_ts(settings, english_tutorial, ts_directory):
    """Require the en/tutorial/tutorial.ts store."""
    return store._require_store(english_tutorial,
                                ts_directory,
                                'tutorial.ts')

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


@pytest.fixture(params=FILE_IMPORT_FAIL_TESTS.keys())
def file_import_failure(request):
    from import_export import exceptions

    return (
        request.param,
        getattr(
            exceptions, FILE_IMPORT_FAIL_TESTS[request.param]))


@pytest.fixture
def ts_directory(po_directory, request, tmpdir, settings):
    """Sets up a tmp directory for TS files. Although it doesnt use the
    po_directory fixture it calls it first to ensure FS is true to the DB
    when fixture is run
    """

    import pytest_pootle

    from pootle_store.models import fs

    ts_dir = str(tmpdir.mkdir("ts"))

    # Adjust locations
    settings.POOTLE_TRANSLATION_DIRECTORY = ts_dir
    fs.location = ts_dir

    shutil.copytree(
        os.path.join(
            os.path.dirname(pytest_pootle.__file__),
            "data", "ts", "tutorial"),
        os.path.join(
            settings.POOTLE_TRANSLATION_DIRECTORY,
            "tutorial"))

    def _cleanup():
        for f in tmpdir.listdir():
            f.remove()
    request.addfinalizer(_cleanup)
    return settings.POOTLE_TRANSLATION_DIRECTORY


@pytest.fixture
def en_tutorial_ts(english_tutorial, ts_directory):
    """Require the en/tutorial/tutorial.ts store."""
    from pootle_format.models import Format

    english_tutorial.project.filetypes.add(
        Format.objects.get(name="ts"))
    return store._require_store(english_tutorial,
                                ts_directory,
                                'tutorial.ts')


@pytest.fixture(
    params=[
        "language0_project0", "templates_project0", "en_terminology"])
def import_tps(request):
    """List of required translation projects for import tests."""
    from pootle_translationproject.models import TranslationProject

    language_code, project_code = request.param.split('_')
    try:
        return TranslationProject.objects.get(language__code=language_code,
                                              project__code=project_code)
    except TranslationProject.DoesNotExist:
        return request.getfuncargvalue(request.param)

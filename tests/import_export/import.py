#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
import pytest

from django.core.files.uploadedfile import SimpleUploadedFile

from import_export.utils import import_file

TEST_PO_DIR = "tests/data/po/tutorial/en"
IMPORT_SUCCESS = "headers_correct.po"
IMPORT_UNSUPP_FILE = "tutorial.ts"
IMPORT_UNSUPP_ERROR_MSG = ("Unsupported filetype '%s', only po files are "
                           + "supported at this time\n")


def _import_file(file_name, file_dir=TEST_PO_DIR,
                 content_type="text/x-gettext-translation"):
    with open(os.path.join(file_dir, file_name), "r") as f:
        import_file(SimpleUploadedFile(file_name,
                                       f.read(),
                                       content_type))


@pytest.mark.django_db
def test_import_success(en_tutorial_po):
    _import_file(IMPORT_SUCCESS)


@pytest.mark.django_db
def test_import_failure(file_import_failure, en_tutorial_po):
    filename, response = file_import_failure
    with pytest.raises(ValueError) as e:
        _import_file(filename)
    assert e.value.message == response % filename


@pytest.mark.django_db
def test_import_unsupported(en_tutorial_ts, ts_directory):
    with pytest.raises(ValueError) as e:
        _import_file(IMPORT_UNSUPP_FILE,
                     file_dir=os.path.join(ts_directory, "tutorial/en"),
                     content_type="text/vnd.trolltech.linguist")
    assert e.value.message == IMPORT_UNSUPP_ERROR_MSG % IMPORT_UNSUPP_FILE

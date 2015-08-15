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

from pootle_store.models import Unit
from import_export.utils import import_file

TEST_DATA_DIR = "tests/data/po/tutorial/en"
IMPORT_SUCCESS = "headers_correct.po"
IMPORT_FAILURE = [(u"revision_header_missing.po",
                   u"File '%s' missing or invalid X-Pootle-Revision header\n"),
                  (u"revision_header_invalid.po",
                   u"File '%s' missing or invalid X-Pootle-Revision header\n"),
                  ("path_header_missing.po",
                   u"File '%s' missing X-Pootle-Path header\n"),
                  ("path_header_invalid.po",
                   u"Could not create '%s'. Missing Project/Language? (Store has no parent.)")]


def _import_file(file_name, content_type="text/x-gettext-translation"):
    with open(os.path.join(TEST_DATA_DIR, file_name), "r") as pofile:
        import_file(SimpleUploadedFile(file_name,
                                       pofile.read(),
                                       content_type=content_type))


@pytest.fixture(params=IMPORT_FAILURE)
def file_import_failure(request):
    return request.param


@pytest.mark.django_db
def test_import_failure(file_import_failure, en_tutorial_po):
    filename, response = file_import_failure
    with pytest.raises(ValueError) as e:
        _import_file(filename)
    assert e.value.message == response % filename


@pytest.mark.django_db
def test_import_success(en_tutorial_po):
    _import_file(IMPORT_SUCCESS)

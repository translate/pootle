# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest


@pytest.fixture
def store_fs_file(settings, tmpdir, test_fs):
    from pootle_fs.files import FSFile
    from pootle_fs.models import StoreFS
    from pootle_project.models import Project

    settings.POOTLE_FS_WORKING_PATH = os.path.join(str(tmpdir), "fs_file_test")
    project = Project.objects.get(code="project0")
    pootle_path = "/language0/%s/example.po" % project.code
    fs_path = "/some/fs/example.po"
    store_fs = StoreFS.objects.create(
        path=fs_path,
        pootle_path=pootle_path)
    fs_file = FSFile(store_fs)
    os.makedirs(os.path.dirname(fs_file.file_path))
    with test_fs.open("data/po/complex.po") as src:
        with open(fs_file.file_path, "w") as target:
            data = src.read()
            target.write(data)
    return fs_file


@pytest.fixture
def store_fs_file_store(settings, tmpdir, tp0_store, test_fs):
    from pootle_fs.files import FSFile
    from pootle_fs.models import StoreFS

    settings.POOTLE_FS_WORKING_PATH = os.path.join(str(tmpdir), "fs_file_test")
    fs_path = "/some/fs/example.po"
    store_fs = StoreFS.objects.create(
        path=fs_path,
        store=tp0_store)
    fs_file = FSFile(store_fs)
    with test_fs.open("data/po/complex.po") as src:
        tp0_store.update(tp0_store.deserialize(src.read()))
    return fs_file

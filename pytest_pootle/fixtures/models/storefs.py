# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os
from collections import OrderedDict

import pytest


TRANSLATION_PATHS = OrderedDict(
    [("default", "gnu_style/po/<language_code>.<ext>"),
     ("subdir1",
      "gnu_style_named_folders/po-<filename>/<language_code>.<ext>"),
     ("subdir2",
      "gnu_style_named_files/po/<filename>-<language_code>.<ext>"),
     ("subdir3",
      "non_gnu_style/locales/<language_code>/<dir_path>/<filename>.<ext>")])


@pytest.fixture
def pootle_fs_working_path(settings, tmpdir):
    settings.POOTLE_FS_WORKING_PATH = str(tmpdir)
    return str(tmpdir)


@pytest.fixture
def fs_src(pootle_fs_working_path):
    src_path = os.path.join(pootle_fs_working_path, "__src__")
    os.mkdir(src_path)
    return src_path


@pytest.fixture
def tp0_store(po_directory, settings, tp0, fs_src):
    from pootle_config.utils import ObjectConfig

    from .store import _require_store

    conf = ObjectConfig(tp0.project)

    conf["pootle_fs.fs_type"] = "localfs"
    conf["pootle_fs.fs_url"] = fs_src
    conf["pootle_fs.translation_mappings"] = OrderedDict(TRANSLATION_PATHS)
    return _require_store(
        tp0,
        settings.POOTLE_TRANSLATION_DIRECTORY, 'project0_fs.po')


@pytest.fixture
def tp0_store_fs(tp0_store):
    """Require the /en/project0/project0.po store."""
    from pootle_fs.models import StoreFS

    return StoreFS.objects.create(
        store=tp0_store,
        path="/some/fs/path")

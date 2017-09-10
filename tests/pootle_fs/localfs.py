# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import os

import pytest

from pootle_fs.utils import FSPlugin


@pytest.mark.django_db
def test_fs_localfs_path(settings, project0):
    project0.config["pootle_fs.fs_url"] = (
        "{POOTLE_TRANSLATION_DIRECTORY}%s"
        % project0.code)
    plugin = FSPlugin(project0)
    assert (
        plugin.fs_url
        == os.path.join(
            settings.POOTLE_TRANSLATION_DIRECTORY,
            project0.code))

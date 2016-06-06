# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest

from pootle.core.plugin import provider
from pootle_fs.delegate import fs_plugins
from pootle_fs.localfs import LocalFSPlugin
from pootle_fs.plugin import Plugin


@pytest.mark.django_db
def test_local_plugin_provider():
    assert fs_plugins.gather()["localfs"] == LocalFSPlugin


@pytest.mark.django_db
def test_plugin_providers():

    class CustomPlugin(Plugin):
        pass

    @provider(fs_plugins)
    def custom_fs_plugin(**kwargs):
        return dict(custom=CustomPlugin)

    assert fs_plugins.gather()["custom"] == CustomPlugin

# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import pytest


@pytest.fixture
def no_fs_files(request):
    from pootle_fs.delegate import fs_file

    file_receivers = fs_file.receivers
    fs_file.receivers = []

    def reconnect():
        fs_file.receivers = file_receivers
    request.addfinalizer(reconnect)


@pytest.fixture
def no_fs_plugins(request):
    from pootle_fs.delegate import fs_plugins

    plugins_receivers = fs_plugins.receivers
    fs_plugins.receivers = []

    def reconnect():
        fs_plugins.receivers = plugins_receivers
    request.addfinalizer(reconnect)


@pytest.fixture
def no_fs_finder(request):
    from pootle_fs.delegate import fs_finder

    finder_receivers = fs_finder.receivers
    fs_finder.receivers = []

    def reconnect():
        fs_finder.receivers = finder_receivers
    request.addfinalizer(reconnect)

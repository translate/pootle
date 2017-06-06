# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from contextlib import contextmanager

import pytest
from pytest_pootle.utils import suppress_getter, suppress_provider

from pootle_fs.delegate import fs_file, fs_finder, fs_plugins


@contextmanager
def _no_fs_files():
    with suppress_getter(fs_file):
        yield


@pytest.fixture
def no_fs_files():
    return _no_fs_files


@contextmanager
def _no_fs_plugins():
    with suppress_provider(fs_plugins):
        yield


@pytest.fixture
def no_fs_plugins():
    return _no_fs_plugins


@contextmanager
def _no_fs_finder():
    with suppress_getter(fs_finder):
        yield


@pytest.fixture
def no_fs_finder():
    return _no_fs_finder


@pytest.fixture
def dummy_fs_files(request):
    fs_file_receivers = fs_file.receivers
    fs_file_receiver_cache = fs_file.sender_receivers_cache.copy()
    fs_file.receivers = []
    fs_file.sender_receivers_cache.clear()

    def _restore_plugins():
        fs_file.sender_receivers_cache = fs_file_receiver_cache
        fs_file.receivers = fs_file_receivers
    request.addfinalizer(_restore_plugins)


@pytest.fixture
def dummy_fs_finder(request):
    fs_finder_receivers = fs_finder.receivers
    fs_finder_receiver_cache = fs_finder.sender_receivers_cache.copy()
    fs_finder.receivers = []
    fs_finder.sender_receivers_cache.clear()

    def _restore_plugins():
        fs_finder.sender_receivers_cache = fs_finder_receiver_cache
        fs_finder.receivers = fs_finder_receivers
    request.addfinalizer(_restore_plugins)


@pytest.fixture
def dummy_fs_plugins(request):
    fs_plugins_receivers = fs_plugins.receivers
    fs_plugins_receiver_cache = fs_plugins.sender_receivers_cache.copy()
    fs_plugins.receivers = []
    fs_plugins.sender_receivers_cache.clear()

    def _restore_plugins():
        fs_plugins.sender_receivers_cache = fs_plugins_receiver_cache
        fs_plugins.receivers = fs_plugins_receivers
    request.addfinalizer(_restore_plugins)


@pytest.fixture
def dummy_fs_getters(dummy_fs_plugins, dummy_fs_files):
    pass

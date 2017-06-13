# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pkgutil import iter_modules

import pytest

from . import fixtures
from .fixtures import (
    core as fixtures_core, formats as fixtures_formats,
    models as fixtures_models, pootle_fs as fixtures_fs)
from .fixtures.core import (
    management as fixtures_core_management, utils as fixtures_core_utils)


def _load_fixtures(*modules):
    for mod in modules:
        path = mod.__path__
        prefix = '%s.' % mod.__name__

        for loader_, name, is_pkg in iter_modules(path, prefix):
            if not is_pkg:
                yield name


def pytest_addoption(parser):
    parser.addoption(
        "--debug-tests",
        action="store",
        default="",
        help="Debug tests to a given file")
    parser.addoption(
        "--force-migration",
        action="store_true",
        default=False,
        help="Force migration before test run")
    parser.addoption(
        "--memusage",
        action="store_true",
        default=False,
        help="Run memusage tests")


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "pootle_vfolders: requires special virtual folder projects")
    config.addinivalue_line(
        "markers", "pootle_memusage: memory usage tests")
    pytest_plugins = tuple(
        _load_fixtures(
            fixtures,
            fixtures_core,
            fixtures_core_management,
            fixtures_core_utils,
            fixtures_formats,
            fixtures_models,
            fixtures_fs))
    for plugin in pytest_plugins:
        config.pluginmanager.import_plugin(plugin)


def pytest_runtest_setup(item):
    marker = item.get_marker("pootle_memusage")
    if marker is not None and not item.config.getoption("--memusage"):
        pytest.skip("test requires memusage flag")

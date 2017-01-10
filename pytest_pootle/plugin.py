# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

from pkgutil import iter_modules

from . import fixtures
from .fixtures import models as fixtures_models
from .fixtures.core import management as fixtures_core_management
from .fixtures.core import utils as fixtures_core_utils
from .fixtures import formats as fixtures_formats
from .fixtures import pootle_fs as fixtures_fs


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


def pytest_configure(config):
    # register an additional marker
    config.addinivalue_line(
        "markers", "pootle_vfolders: requires special virtual folder projects")

    pytest_plugins = tuple(
        _load_fixtures(
            fixtures,
            fixtures_core_management,
            fixtures_core_utils,
            fixtures_formats,
            fixtures_models,
            fixtures_fs))
    for plugin in pytest_plugins:
        config.pluginmanager.import_plugin(plugin)

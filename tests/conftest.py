#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014-2015 Evernote Corporation
#
# This file is part of Pootle.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

import os
from pkgutil import iter_modules

from django import setup
from django.conf import settings

from . import fixtures
from .fixtures import models as fixture_models


def pytest_configure():
    if not settings.configured:
        from pootle import syspath_override  # Needed for monkey-patching
        os.environ['DJANGO_SETTINGS_MODULE'] = 'pootle.settings'
        WORKING_DIR = os.path.abspath(os.path.dirname(__file__))
        os.environ['POOTLE_SETTINGS'] = os.path.join(WORKING_DIR, 'settings.py')
        setup()  # Required until pytest-dev/pytest-django#146 is fixed


def _load_fixtures(*modules):
    for mod in modules:
        path = mod.__path__
        prefix = '%s.' % mod.__name__

        for loader, name, is_pkg in iter_modules(path, prefix):
            if not is_pkg:
                yield name


pytest_plugins = tuple(_load_fixtures(fixtures, fixture_models), )

#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
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
import glob

DEFAULT_TEST_SETTINGS = ['90-tests.conf', '90-tests-local.conf']

WORKING_DIR = os.path.abspath(os.path.dirname(__file__))
ROOT_DIR = os.path.dirname(WORKING_DIR)


def working_path(filename):
    """Return an absolute path for :param:`filename` by joining it to
    ``WORKING_DIR``."""
    return os.path.join(WORKING_DIR, filename)


def root_path(filename):
    """Return an absolute path for :param:`filename` by joining it to
    ``ROOT_DIR``."""
    return os.path.join(ROOT_DIR, filename)


def remove_custom_settings(file_path):
    """Removes any custom `90-*.conf` files that are NOT meant to be
    used during testing.
    """
    path, name = os.path.split(file_path)
    return not name.startswith('90-') or name in test_settings_files


def remove_testing_settings(file_path):
    """Removes any `90-tests(-local).conf` files."""
    path, name = os.path.split(file_path)
    return name not in DEFAULT_TEST_SETTINGS


test_settings_files = []
test_settings = os.environ.get('POOTLE_SETTINGS_TESTS', '')

if test_settings:
    test_settings_files = DEFAULT_TEST_SETTINGS + [
        test_settings,
        '%s-local%s' % os.path.splitext(test_settings),
    ]

conf_files_path = os.path.join(WORKING_DIR, 'settings', '*.conf')
conf_files = glob.glob(conf_files_path)

if test_settings_files:
    # XXX: should it abort if none of the test settings have been found?
    conf_files = filter(remove_custom_settings, conf_files)
else:
    conf_files = filter(remove_testing_settings, conf_files)

conf_files.sort()

for f in conf_files:
    execfile(os.path.abspath(f))

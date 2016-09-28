# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

import glob
import os
import importlib

WORKING_DIR = os.path.abspath(os.path.dirname(__file__))


def working_path(filename):
    """Return an absolute path for :param:`filename` by joining it to
    ``WORKING_DIR``.
    """
    return os.path.join(WORKING_DIR, filename)


def app_path(app_name):
    """Return an absolute path for installed :param:`app_name`"""
    app_module = importlib.import_module(app_name)
    return os.path.dirname(app_module.__file__)


conf_files_path = os.path.join(WORKING_DIR, 'settings', '*.conf')
conf_files = glob.glob(conf_files_path)
conf_files.sort()

for f in conf_files:
    execfile(os.path.abspath(f))

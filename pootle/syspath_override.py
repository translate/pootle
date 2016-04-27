# -*- coding: utf-8 -*-
#
# Copyright (C) Pootle contributors.
#
# This file is a part of the Pootle project. It is distributed under the GPL3
# or later license. See the LICENSE file for a copy of the license and the
# AUTHORS file for copyright and authorship information.

"""Adds pootle directories to the python import path"""

# FIXME: is this useful on an installed codebase or only when running from
# source?

import os
import sys


ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
POOTLE_DIR = os.path.abspath(os.path.dirname(__file__))
sys.path.insert(0, ROOT_DIR)  # Top level directory
sys.path.insert(0, POOTLE_DIR)  # Pootle directory

sys.path.insert(0, os.path.join(POOTLE_DIR, 'apps'))  # Applications

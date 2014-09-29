#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2008 Zuza Software Foundation
#
# This file is part of translate.
#
# translate is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# translate is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with translate; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

""" Adds pootle directories to the python import path """

#FIXME: is this useful on an installed codebase or only when running
# from source?

import os
import sys

ROOT_DIR = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
POOTLE_DIR = os.path.abspath(os.path.dirname(__file__))
POOTLE_APPS = os.path.join(POOTLE_DIR, 'apps')

sys.path.insert(0, ROOT_DIR)  # Top level directory.
sys.path.insert(0, POOTLE_DIR)  # Pootle directory.
sys.path.insert(0, POOTLE_APPS)  # Pootle applications.

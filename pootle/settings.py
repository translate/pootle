#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2013 Zuza Software Foundation
# Copyright 2014 Evernote Corporation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify it under the
# terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# Pootle is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR
# A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# Pootle; if not, see <http://www.gnu.org/licenses/>.

import os
import glob

WORKING_DIR = os.path.abspath(os.path.dirname(__file__))


def working_path(filename):
    """Return an absolute path for :param:`filename` by joining it to
    ``WORKING_DIR``."""
    return os.path.join(WORKING_DIR, filename)


conf_files_path = os.path.join(WORKING_DIR, 'settings', '*.conf')
conf_files = glob.glob(conf_files_path)
conf_files.sort()

for f in conf_files:
    execfile(os.path.abspath(f))

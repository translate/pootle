# -*- coding: utf-8 -*-
#
# Copyright 2011, 2013 Zuza Software Foundation
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
import tempfile

from django.conf import settings


def mkstemp(*args, **kwargs):
    """Wrap tempfile.mkstemp, setting the permissions of the created temporary
    file as specified in settings (see bug 1983).
    """
    fd, name = tempfile.mkstemp(*args, **kwargs)
    if hasattr(os, 'fchmod'):
        os.fchmod(fd, settings.EXPORTED_FILE_MODE)
    else:
        os.chmod(name, settings.EXPORTED_FILE_MODE)
    return fd, name


def mkdtemp(*args, **kwargs):
    """Wrap tempfile.mkdtemp, setting the permissions of the created temporary
    file as specified in settings (see bug 1983).
    """
    name = tempfile.mkdtemp(*args, **kwargs)
    os.chmod(name, settings.EXPORTED_DIRECTORY_MODE)
    return name

# -*- coding: utf-8 -*-
#
# Copyright 2012 Zuza Software Foundation
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

"""Utility functions to help with version control systems."""

import os.path

from translate.storage import versioncontrol

from django.conf import settings

from pootle_store.util import relative_real_path


def to_vcs_path(path):
    path = relative_real_path(path)
    return os.path.join(settings.PODIRECTORY, path)


def hasversioning(path):
    path = to_vcs_path(path)
    return versioncontrol.hasversioning(path, settings.PODIRECTORY)


def commit_file(path, message, author):
    vcs_path = to_vcs_path(path)
    versioncontrol.commitfile(vcs_path, message=message, author=author)


def update_file(path):
    vcs_path = to_vcs_path(path)
    versioncontrol.updatefile(vcs_path)


def add_files(path, files, message):
    vcs_path = to_vcs_path(path)
    vcs = versioncontrol.get_versioned_object(vcs_path)
    output = vcs.add([to_vcs_path(f) for f in files], message)
    return output

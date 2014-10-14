#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009-2012 Zuza Software Foundation
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
from pootle_store.util import add_trailing_slash
from pootle_misc import versioncontrol


def recursive_files_and_dirs(ignored_files, ext, real_dir, file_filter):
    """Traverses :param:`real_dir` searching for files and directories.

    :param ignored_files: List of files that will be ignored.
    :param ext: Only files ending with this extension will be considered.
    :param real_dir:
    :param file_filter: Filtering function applied to the list of files found.
    :return: A tuple of lists of files and directories found when traversing the
        given path and after applying the given restrictions.
    """
    real_dir = add_trailing_slash(real_dir)
    files = []
    dirs = []

    for _path, _dirs, _files in os.walk(real_dir, followlinks=True):
        # Make it relative:
        _path = _path[len(real_dir):]
        files += [os.path.join(_path, f) for f in filter(file_filter, _files)
                  if f.endswith(ext) and f not in ignored_files]

        # Edit _dirs in place to avoid further recursion into hidden directories
        for d in _dirs:
            if is_hidden_file(d):
                _dirs.remove(d)

        dirs += _dirs

    return files, dirs


def sync_from_vcs(ignored_files, ext, relative_dir,
                  file_filter=lambda _x: True):
    """Recursively synchronise the PO directory from the VCS directory.

    This brings over files from VCS, and removes files in PO directory that
    were removed in VCS.
    """
    if not versioncontrol.hasversioning(relative_dir):
        return

    podir_path = versioncontrol.to_podir_path(relative_dir)
    vcs_path = versioncontrol.to_vcs_path(relative_dir)
    vcs_files, vcs_dirs = recursive_files_and_dirs(ignored_files, ext,
                                                   vcs_path, file_filter)
    files, dirs = recursive_files_and_dirs(ignored_files, ext, podir_path,
                                           file_filter)

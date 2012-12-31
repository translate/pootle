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
import shutil

from translate.storage import versioncontrol

from django.conf import settings

from pootle_store.util import relative_real_path


def to_vcs_path(path):
    # FIXME: this is ignoring symlinks!
    path = relative_real_path(path)
    return os.path.join(settings.VCS_DIRECTORY, path)


def to_podir_path(path):
    path = relative_real_path(path)
    return os.path.join(settings.PODIRECTORY, path)


def hasversioning(path):
    path = to_vcs_path(path)
    return versioncontrol.hasversioning(path, settings.VCS_DIRECTORY)


def commit_file(path, message, author):
    vcs_path = to_vcs_path(path)
    path = to_podir_path(path)
    shutil.copy2(path, vcs_path)
    versioncontrol.commitfile(vcs_path, message=message, author=author)


def copy_to_podir(path):
    """Copy the given path from the VCS directory to the PO directory."""
    vcs_path = to_vcs_path(path)
    path = to_podir_path(path)
    shutil.copy2(vcs_path, path)


def update_file(path):
    vcs_path = to_vcs_path(path)
    path = to_podir_path(path)
    versioncontrol.updatefile(vcs_path)
    shutil.copy2(vcs_path, path)


def update_dir(path):
    """Updates a whole directory without syncing with the po directory.

    This assumes that we can update cleanly, and must be followed by
    :meth:`~pootle_translationproject.models.TranslationProject.scan_files`
    since the podirectory isn't updated as part of this call.

    For some systems (like git) this can cause the rest of a cloned repository
    to be updated as well, so changes might not be limited to the given path.
    """
    vcs_path = to_vcs_path(path)
    vcs_object = versioncontrol.get_versioned_object(vcs_path)
    vcs_object.update(needs_revert=False)


def add_files(path, files, message, author=None):
    vcs_path = to_vcs_path(path)
    path = to_podir_path(path)
    vcs = versioncontrol.get_versioned_object(vcs_path)
    #: list of (podir_path, vcs_path) tuples
    file_paths = [(to_podir_path(f), to_vcs_path(f)) for f in files]
    for podir_path, vcs_path in file_paths:
        vcs_dir = os.path.dirname(vcs_path)
        if not os.path.exists(vcs_dir):
            os.makedirs(vcs_dir)
        shutil.copy(podir_path, vcs_path)
    output = vcs.add([to_vcs_path(f) for f in files], message, author)
    return output

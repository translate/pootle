#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2004-2007 Zuza Software Foundation
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


import translate.storage.versioncontrol
from translate.storage.versioncontrol import run_command
from translate.storage.versioncontrol import GenericRevisionControlSystem

class bzr(GenericRevisionControlSystem):
    """Class to manage items under revision control of bzr."""

    RCS_METADIR = ".bzr"
    SCAN_PARENTS = True
    
    def update(self, revision=None):
        """Does a clean update of the given path"""
        # bzr revert
        command = ["bzr", "revert", self.location_abs]
        exitcode, output_revert, error = run_command(command)
        if exitcode != 0:
            raise IOError("[BZR] revert of '%s' failed: %s" \
                    % (self.location_abs, error))
        # bzr pull
        command = ["bzr", "pull"]
        exitcode, output_pull, error = run_command(command)
        if exitcode != 0:
            raise IOError("[BZR] pull of '%s' failed: %s" \
                    % (self.location_abs, error))
        return output_revert + output_pull

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        # bzr commit
        command = ["bzw", "commit"]
        if message:
            command.extend(["-m", message])
        # the filename is the last argument
        command.append(self.location_abs)
        exitcode, output_commit, error = run_command(command)
        if exitcode != 0:
            raise IOError("[BZR] commit of '%s' failed: %s" \
                    % (self.location_abs, error))
        # bzr push
        command = ["bzr", "push"]
        exitcode, output_push, error = run_command(command)
        if exitcode != 0:
            raise IOError("[BZR] push of '%s' failed: %s" \
                    % (self.location_abs, error))
        return output_commit + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the bzr repository"""
        # bzr cat
        command = ["bzr", "cat", self.location_abs]
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[BZR] cat failed for '%s': %s" \
                    % (self.location_abs, error))
        return output


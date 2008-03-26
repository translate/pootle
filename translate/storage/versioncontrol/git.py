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


from translate.storage.versioncontrol import run_command
from translate.storage.versioncontrol import GenericRevisionControlSystem

class git(GenericRevisionControlSystem):
    """Class to manage items under revision control of git."""

    RCS_METADIR = ".git"
    SCAN_PARENTS = True

    def _get_git_dir(self):
        """git requires the git metadata directory for every operation
        """
        import os
        return os.path.join(self.root_dir, self.RCS_METADIR)
    
    def update(self, revision=None):
        """Does a clean update of the given path"""
        # git checkout
        command = ["git", "--git-dir", self._get_git_dir(),
                "checkout", self.location_rel]
        exitcode, output_checkout, error = run_command(command)
        if exitcode != 0:
            raise IOError("[GIT] checkout failed (%s): %s" % (command, error))
        # pull changes
        command = ["git", "--git-dir", self._get_git_dir(), "pull"]
        exitcode, output_pull, error = run_command(command)
        if exitcode != 0:
            raise IOError("[GIT] pull failed (%s): %s" % (command, error))
        return output_checkout + output_pull

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        # add the file
        command = ["git", "--git-dir", self._get_git_dir(),
                "add", self.location_rel]
        exitcode, output_add, error = run_command(command)
        if exitcode != 0:
            raise IOError("[GIT] add of ('%s', '%s') failed: %s" \
                    % (self.root_dir, self.location_rel, error))
        # commit file
        command = ["git", "--git-dir", self._get_git_dir(), "commit"]
        if message:
            command.extend(["-m", message])
        exitcode, output_commit, error = run_command(command)
        if exitcode != 0:
            raise IOError("[GIT] commit of ('%s', '%s') failed: %s" \
                    % (self.root_dir, self.location_rel, error))
        # push changes
        command = ["git", "--git-dir", self._get_git_dir(), "push"]
        exitcode, output_push, error = run_command(command)
        if exitcode != 0:
            raise IOError("[GIT] push of ('%s', '%s') failed: %s" \
                    % (self.root_dir, self.location_rel, error))
        return output_add + output_commit + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the git repository"""
        # run git-show
        command = ["git", "--git-dir", self._get_git_dir(), "show",
                "HEAD:%s" % self.location_rel]
        exitcode, output, error = run_command(command)
        if exitcode != 0:
            raise IOError("[GIT] 'show' failed for ('%s', %s): %s" \
                    % (self.root_dir, self.location_rel, error))
        return output


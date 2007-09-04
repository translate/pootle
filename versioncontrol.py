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

"""This module manages interaction with version control systems.

To implement support for a new version control system, override the class
GenericVersionControlSystem. 

TODO:
    * move to the translate toolkit and split into different files
"""

import re
import os

# The subprocess module allows to use cross-platform command execution without 
# using the shell (which increases security).
# p = subprocess.Popen(shell=False, close_fds=True, stdin=subprocess.PIPE,
#       stdout=subprocess.PIPE, stderr=subprocess.PIPE, args = command)
# This is only available since python 2.4, so we won't rely on it yet.
try:
    import subprocess

    def pipe(command):
        """Runs a command (array of program name and arguments) and returns the
        exitcode, the output and the error as a tuple.
        """
        # ok - we use "subprocess"
        proc = subprocess.Popen(args = command,
                stdout = subprocess.PIPE,
                stderr = subprocess.PIPE,
                stdin = subprocess.PIPE)
        (output, error) = proc.communicate()
        ret = proc.returncode
        return ret, output, error

except ImportError:
    # fallback for python < 2.4
    import popen2

    def pipe(command):
        """Runs a command (array of program name and arguments) and returns the
        exitcode, the output and the error as a tuple.
        """
        escaped_command = " ".join([shellescape(arg) for arg in command])
        proc = popen2.Popen3(escaped_command, True)
        (c_stdin, c_stdout, c_stderr) = (proc.tochild, proc.fromchild, proc.childerr)
        output = c_stdout.read()
        error = c_stderr.read()
        ret = proc.wait()
        c_stdout.close()
        c_stderr.close()
        c_stdin.close()
        return ret, output, error

def shellescape(path):
    """Shell-escape any non-alphanumeric characters."""
    return re.sub(r'(\W)', r'\\\1', path)


class GenericVersionControlSystem:
    """The super class for all version control classes."""

    # as long as noone overrides this, the test below always succeeds
    MARKER_DIR = os.path.curdir

    def __init__(self, location):
        """Default version control checker: test if self.MARKER_DIR exists.
        
        Most version control systems depend on the existence of a specific 
        directory thus you will most likely not need to touch this check - just 
        call it. The IOError exception indicates that the specified file is not 
        controlled by the given version control system.
        """
        parent_dir = os.path.dirname(os.path.abspath(location))
        if not os.path.isdir(os.path.join(parent_dir, self.MARKER_DIR)):
            raise IOError("Could not find version control information: %s" % location)


class CVS(GenericVersionControlSystem):
    """Class to manage items under revision control of CVS."""

    MARKER_DIR = "CVS"

    def __init__(self, location):
        GenericVersionControlSystem.__init__(self, location)
        self.cvsdir = os.path.join(os.path.dirname(os.path.abspath(location)),
                self.MARKER_DIR)
        self.location = os.path.abspath(location)

    def _readfile(self, cvsroot, path, revision=None):
        """
        Read a single file from the CVS repository without checking out a full 
        working directory.
        
        @param: cvsroot: the CVSROOT for the repository
        @param path: path to the file relative to cvs root
        @param revision: revision or tag to get (retrieves from HEAD if None)
        """
        if revision:
            command = ["cvs", "-d", cvsroot, "-Q", "co", "-p" "-r",
                    revision, path]
        else:
            command = ["cvs", "-d", cvsroot, "-Q", "co", "-p", path]
        exitcode, output, error = pipe(command)
        if exitcode != 0:
            raise IOError("[CVS] Could not read '%s' from '%s': %s / %s" % \
                    (path, cvsroot, output, error))
        return output

    def getcleanfile(self, revision=None):
        """Get the content of the file for the given revision"""
        parentdir = os.path.dirname(self.location)
        cvsdir = os.path.join(parentdir, "CVS")
        cvsroot = open(os.path.join(cvsdir, "Root"), "r").read().strip()
        cvspath = open(os.path.join(cvsdir, "Repository"), "r").read().strip()
        cvsfilename = os.path.join(cvspath, os.path.basename(self.location))
        if revision is None:
            cvsentries = open(os.path.join(cvsdir, "Entries"), "r").readlines()
            revision = self._getcvstag(cvsentries)
        if revision == "BASE":
            cvsentries = open(os.path.join(cvsdir, "Entries"), "r").readlines()
            revision = self._getcvsrevision(cvsentries)
        return self._readfile(cvsroot, cvsfilename, revision)

    def update(self, revision=None):
        """Does a clean update of the given path"""
        working_dir = os.path.dirname(self.location)
        filename = os.path.basename(self.location)
        filename_backup = filename + os.path.extsep + "bak"
        original_dir = os.getcwd()
        if working_dir:
            try:
                # first: check if we are allowed to _change_ to the current dir
                # (of course, we are already here, but that does not mean so much)
                os.chdir(original_dir)
            except OSError, error:
                raise IOError("[CVS] could not change to directory (%s): %s" \
                        % (original_dir, error))
            try:
                # change to the parent directory of the CVS managed file
                os.chdir(working_dir)
            except OSError, error:
                raise IOError("[CVS] could not change to directory (%s): %s" \
                        % (working_dir, error))
        try:
            os.rename(filename, filename_backup)
        except OSError, error:
            # something went wrong - go back to the original directory
            try:
                os.chdir(original_dir)
            except OSError:
                pass
            raise IOError("[CVS] could not move the file '%s' to '%s': %s" % \
                    (filename, filename_backup, error))
        if revision:
            command = ["cvs", "-Q", "update", "-C", "-r", revision, filename]
        else:
            command = ["cvs", "-Q", "update", "-C", filename]
        exitcode, output, error = pipe(command)
        # restore backup in case of an error - remove backup for success
        try:
            if error:
                os.rename(filename_backup, filename)
            else:
                os.remove(filename_backup)
        except OSError:
            pass
        # always go back to the original directory
        try:
            os.chdir(original_dir)
        except OSError:
            pass
        # raise an error or return successfully - depending on the CVS command
        if exitcode != 0:
            raise IOError("[CVS] Error running CVS command '%s': %s" % (command, error))
        else:
            return output

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        working_dir = os.path.dirname(self.location)
        filename = os.path.basename(self.location)
        original_dir = os.getcwd()
        if working_dir:
            try:
                # first: check if we are allowed to _change_ to the current dir
                # (of course, we are already here, but that does not mean so much)
                os.chdir(original_dir)
            except OSError, error:
                raise IOError("[CVS] could not change to directory (%s): %s" \
                        % (original_dir, error))
            try:
                # change to the parent directory of the CVS managed file
                os.chdir(working_dir)
            except OSError, error:
                raise IOError("[CVS] could not change to directory (%s): %s" \
                        % (working_dir, error))
        if message:
            command = ["cvs", "-Q", "commit", "-m", message, filename]
        elif message is None:
            command = ["cvs", "-Q", "commit", filename]
        exitcode, output, error = pipe(command)
        # always go back to the original directory
        try:
            os.chdir(original_dir)
        except OSError:
            pass
        # raise an error or return successfully - depending on the CVS command
        if exitcode != 0:
            raise IOError("[CVS] Error running CVS command '%s': %s" % (command, error))
        else:
            return output

    def _getcvsrevision(self, cvsentries):
        """returns the revision number the file was checked out with by looking
        in the lines of cvsentries
        """
        filename = os.path.basename(self.location)
        for cvsentry in cvsentries:
            # an entries line looks like the following:
            #  /README.TXT/1.19/Sun Dec 16 06:00:12 2001//
            cvsentryparts = cvsentry.split("/")
            if len(cvsentryparts) < 6:
                continue
            if os.path.normcase(cvsentryparts[1]) == os.path.normcase(filename):
                return cvsentryparts[2].strip()
        return None

    def _getcvstag(self, cvsentries):
        """Returns the sticky tag the file was checked out with by looking in 
        the lines of cvsentries.
        """
        filename = os.path.basename(self.location)
        for cvsentry in cvsentries:
            # an entries line looks like the following:
            #  /README.TXT/1.19/Sun Dec 16 06:00:12 2001//
            cvsentryparts = cvsentry.split("/")
            if len(cvsentryparts) < 6:
                continue
            if os.path.normcase(cvsentryparts[1]) == os.path.normcase(filename):
                if cvsentryparts[5].startswith("T"):
                    return cvsentryparts[5][1:].strip()
        return None


class SVN(GenericVersionControlSystem):
    """Class to manage items under revision control of Subversion."""

    MARKER_DIR = ".svn"

    def __init__(self, location):
        GenericVersionControlSystem.__init__(self, location)
        self.svndir = os.path.join(os.path.dirname(os.path.abspath(location)),
                self.MARKER_DIR)
        self.location = os.path.abspath(location)

    def update(self, revision=None):
        """update the working copy - remove local modifications if necessary"""
        # revert the local copy (remove local changes)
        command = ["svn", "revert", self.location]
        exitcode, output_revert, error = pipe(command)
        # any error messages?
        if error:
            raise IOError("[SVN] Subversion error running '%s': %s" % (command, error))
        # update the working copy to the given revision
        if revision is None:
            command = ["svn", "update", self.location]
        else:
            command = ["svn", "update", "-r", revision, self.location]
        exitcode, output_update, error = pipe(command)
        if exitcode != 0:
            raise IOError("[SVN] Subversion error running '%s': %s" % (command, error))
        return output_revert + output_update

    def commit(self, message=None):
        """commit the file and return the given message if present"""
        if message is None:
            command = ["svn", "-q", "--non-interactive", "commit", self.location]
        else:
            command = ["svn", "-q", "--non-interactive", "commit", "-m",
                    message, self.location]
        exitcode, output, error = pipe(command)
        if exitcode != 0:
            raise IOError("[SVN] Error running SVN command '%s': %s" % (command, error))
        return output
    
    def getcleanfile(self, revision=None):
        """return the content of the 'head' revision of the file"""
        if revision is None:
            command = ["svn", "cat", self.location]
        else:
            command = ["svn", "cat", "-r", revision, self.location]
        exitcode, output, error = pipe(command)
        if exitcode != 0:
            raise IOError("[SVN] Subversion error running '%s': %s" % (command, error))
        return output


class DARCS(GenericVersionControlSystem):
    """Class to manage items under revision control of darcs."""

    # This assumes that the whole PO directory is stored in darcs so we need to 
    # reach the _darcs dir from po/project/language. That results in this 
    # relative path
    MARKER_DIR = "_darcs"
    
    def __init__(self, location):
        self.location = None
        try:
            # this works only, if the po file is in the root of the repository
            GenericVersionControlSystem.__init__(self, location)
            self.darcsdir = os.path.join(os.path.dirname(os.path.abspath(location)),
                    self.MARKER_DIR)
            self.location = os.path.abspath(location)
            # we finished successfully
        except IOError, err_msg:
            # the following code scans all directories above the po file for the
            # common '_darcs' directory
            # first: resolve possible symlinks
            current_dir = os.path.realpath(os.path.dirname(location))
            # avoid any dead loops (could this happen?)
            max_depth = 64
            while not os.path.isdir(os.path.join(current_dir, self.MARKER_DIR)):
                if os.path.dirname(current_dir) == current_dir:
                    # we reached the root directory - stop
                    break
                if max_depth <= 0:
                    # some kind of dead loop or a _very_ deep directory structure
                    break
                # go to the next higher level
                current_dir = os.path.dirname(current_dir)
            else:
                # we found the MARKER_DIR
                self.darcsdir = current_dir
                # retrieve the relative path of the po file based on self.darcsdir
                realpath_pofile = os.path.realpath(location)
                basedir = self.darcsdir + os.path.sep
                if realpath_pofile.startswith(basedir):
                    # remove the base directory (including the trailing slash)
                    self.location = realpath_pofile.replace(basedir, "", 1)
                    # successfully finished
                else:
                    # this should never happen
                    raise IOError("[Darcs] unexpected path names: '%s' and '%s'" \
                            % (self.darcsdir, basedir))
            if self.location is None:
                # we did not find a '_darcs' directory
                raise IOError(err_msg)
                    
    def update(self, revision=None):
        """Does a clean update of the given path
        @param: revision: ignored for darcs
        """
        # TODO: check if 'revert' and 'pull' work without specifying '--repodir'
        # revert local changes (avoids conflicts)
        command = ["darcs", "revert", "-a", self.location]
        exitcode, output_revert, error = pipe(command)
        if exitcode != 0:
            raise IOError("[Darcs] error running '%s': %s" % (command, error))
        # pull new patches
        command = ["darcs", "pull", "-a"]
        exitcode, output_pull, error = pipe(command)
        if exitcode != 0:
            raise IOError("[Darcs] error running '%s': %s" % (command, error))
        return output_revert + output_pull

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        if message is None:
            message = ""
        # set change message
        command = ["darcs", "record", "-a", "--skip-long-comment", "-m",
                message, self.location]
        exitcode, output_record, error = pipe(command)
        if exitcode != 0:
            raise IOError("[Darcs] Error running darcs command '%s': %s" \
                    % (command, error))
        # push changes
        command = ["darcs", "push", "-a"]
        exitcode, output_push, error = pipe(command)
        if exitcode != 0:
            raise IOError("[Darcs] Error running darcs command '%s': %s" \
                    % (command, error))
        return output_record + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the darcs repository
        @param: revision: ignored for darcs
        """
        filename = os.path.join('_darcs', 'pristine', self.location)
        try:
            darcs_file = open(filename)
            output = darcs_file.read()
            darcs_file.close()
        except IOError, error:
            raise IOError("[Darcs] error reading original file '%s': %s" % \
                    (filename, error))
        return output

class GIT(GenericVersionControlSystem):
    """Class to manage items under revision control of git."""

    # This assumes that the whole PO directory is stored in git so we need to 
    # reach the .git dir from po/project/language. That results in this 
    # relative path
    MARKER_DIR = ".git"
    
    def __init__(self, location):
        self.location = None
        try:
            # this works only, if the po file is in the root of the repository
            GenericVersionControlSystem.__init__(self, location)
            self.gitdir = os.path.join(os.path.dirname(os.path.abspath(location)),
                    self.MARKER_DIR)
            self.location = os.path.abspath(location)
            # we finished successfully
        except IOError, err_msg:
            # the following code scans all directories above the po file for the
            # common '.git' directory
            # first: resolve possible symlinks
            current_dir = os.path.realpath(os.path.dirname(location))
            # avoid any dead loops (could this happen?)
            max_depth = 64
            while not os.path.isdir(os.path.join(current_dir, self.MARKER_DIR)):
                if os.path.dirname(current_dir) == current_dir:
                    # we reached the root directory - stop
                    break
                if max_depth <= 0:
                    # some kind of dead loop or a _very_ deep directory structure
                    break
                # go to the next higher level
                current_dir = os.path.dirname(current_dir)
            else:
                # we found the MARKER_DIR
                self.gitdir = current_dir
                # retrieve the relative path of the po file based on self.gitdir
                realpath_pofile = os.path.realpath(location)
                basedir = self.gitdir + os.path.sep
                if realpath_pofile.startswith(basedir):
                    # remove the base directory (including the trailing slash)
                    self.location = realpath_pofile.replace(basedir, "", 1)
                    # successfully finished
                else:
                    # this should never happen
                    raise IOError("[GIT] unexpected path names: '%s' and '%s'" \
                            % (self.gitdir, basedir))
            if self.location is None:
                # we did not find a '.git' directory
                raise IOError(err_msg)
                    
    def update(self, revision=None):
        """Does a clean update of the given path"""
        # git checkout
        command = ["git", "checkout", self.location]
        exitcode, output_checkout, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] checkout failed (%s): %s" % (command, error))
        # pull changes
        command = ["git", "pull"]
        exitcode, output_pull, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] pull failed (%s): %s" % (command, error))
        return output_checkout + output_pull

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        # add the file
        command = ["git", "add", self.location]
        exitcode, output_add, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] add of '%s' failed: %s" % (self.location, error))
        # commit file
        if message is None:
            command = ["git", "commit"]
        else:
            command = ["git", "commit", "-m", message]
        exitcode, output_commit, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] commit of '%s' failed: %s" % (self.location, error))
        # push changes
        command = ["git", "push"]
        exitcode, output_push, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] push of '%s' failed: %s" % (self.location, error))
        return output_add + output_commit + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the git repository"""
        # get ls-tree HEAD
        command = ["git", "ls-tree", "HEAD", self.location]
        exitcode, output_ls, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] ls-tree failed for '%s': %s" \
                    % self.location, error)
        # determine the id
        match = re.search(" ([a-f0-9]{40})\t", output_ls)
        if not match:
            raise IOError("[GIT] failed to get git id for '%s'" % self.location)
        # remove whitespace around
        git_id = match.groups()[0].strip()
        # run cat-file
        command = ["git", "cat-file", "blob", git_id]
        exitcode, output_cat, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] cat-file failed for ('%s', %s): %s" \
                    % (self.location, git_id, error))
        return output_ls + output_cat

class BZR(GenericVersionControlSystem):
    """Class to manage items under revision control of bzr."""

    # This assumes that the whole PO directory is stored in bzr so we need to 
    # reach the .git dir from po/project/language. That results in this 
    # relative path
    MARKER_DIR = ".bzr"
    
    def __init__(self, location):
        self.location = None
        try:
            # this works only, if the po file is in the root of the repository
            GenericVersionControlSystem.__init__(self, location)
            self.bzrdir = os.path.join(os.path.dirname(os.path.abspath(location)),
                    self.MARKER_DIR)
            self.location = os.path.abspath(location)
            # we finished successfully
        except IOError, err_msg:
            # the following code scans all directories above the po file for the
            # common '.bzr' directory
            # first: resolve possible symlinks
            current_dir = os.path.realpath(os.path.dirname(location))
            # avoid any dead loops (could this happen?)
            max_depth = 64
            while not os.path.isdir(os.path.join(current_dir, self.MARKER_DIR)):
                if os.path.dirname(current_dir) == current_dir:
                    # we reached the root directory - stop
                    break
                if max_depth <= 0:
                    # some kind of dead loop or a _very_ deep directory structure
                    break
                # go to the next higher level
                current_dir = os.path.dirname(current_dir)
            else:
                # we found the MARKER_DIR
                self.bzrdir = current_dir
                # retrieve the relative path of the po file based on self.bzrdir
                realpath_pofile = os.path.realpath(location)
                basedir = self.bzrdir + os.path.sep
                if realpath_pofile.startswith(basedir):
                    # remove the base directory (including the trailing slash)
                    self.location = realpath_pofile.replace(basedir, "", 1)
                    # successfully finished
                else:
                    # this should never happen
                    raise IOError("[BZR] unexpected path names: '%s' and '%s'" \
                            % (self.bzrdir, basedir))
            if self.location is None:
                # we did not find a '.bzr' directory
                raise IOError(err_msg)
                    
    def update(self, revision=None):
        """Does a clean update of the given path"""
        # bazaar revert
        command = ["bzr", "revert", self.location]
        exitcode, output_revert, error = pipe(command)
        if exitcode != 0:
            raise IOError("[BZR] revert of '%s' failed: %s" \
                    % (self.location, error))
        # bazaar pull
        command = ["bzr", "pull"]
        exitcode, output_pull, error = pipe(command)
        if exitcode != 0:
            raise IOError("[BZR] pull of '%s' failed: %s" \
                    % (self.location, error))
        return output_revert + output_pull

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        # bzr commit
        if message is None:
            command = ["bzr", "commit", self.location]
        else:
            command = ["bzr", "commit", "-m", message, self.location]
        exitcode, output_commit, error = pipe(command)
        if exitcode != 0:
            raise IOError("[BZR] commit of '%s' failed: %s" \
                    % (self.location, error))
        # bzr push
        command = ["bzr", "push"]
        exitcode, output_push, error = pipe(command)
        if exitcode != 0:
            raise IOError("[BZR] push of '%s' failed: %s" \
                    % (self.location, error))
        return output_commit + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the bzr repository"""
        # bzr cat
        command = ["bzr", "cat", self.location]
        exitcode, output, error = pipe(command)
        if exitcode != 0:
            raise IOError("[BZR] cat failed for '%s': %s" \
                    % (self.location, error))
        return output

# which versioning systems are supported by default?
DEFAULT_VERSIONING_SYSTEMS = [CVS, SVN, DARCS, GIT, BZR]

def get_versioned_object(
        location,
        versioning_systems=DEFAULT_VERSIONING_SYSTEMS,
        follow_symlinks=True):
    """return a versioned object for the given file"""
    # go through all versioning systems and return a versioned object if possible
    for vers_sys in versioning_systems:
        try:
            return vers_sys(location)
        except IOError:
            continue
    # if 'location' is a symlink, then we should try the original file
    if follow_symlinks and os.path.islink(location):
        return get_versioned_object(os.path.realpath(location),
                versioning_systems = versioning_systems,
                follow_symlinks = False)
    # if everything fails:
    raise IOError("Could not find version control information: %s" % location)

# stay compatible to the previous version
def updatefile(filename):
    return get_versioned_object(filename).update()

def getcleanfile(filename, revision=None):
    return get_versioned_object(filename).getcleanfile(revision)

def commitfile(filename, message=None):
    return get_versioned_object(filename).commit(message)

def hasversioning(item):
    try:
        # try all available version control systems
        get_versioned_object(item)
        return True
    except IOError:
        return False
    
if __name__ == "__main__":
    import sys
    filenames = sys.argv[1:]
    for filename in filenames:
        contents = getcleanfile(filename)
        sys.stdout.write(contents)


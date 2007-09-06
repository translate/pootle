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

To implement support for a new version control system, inherit the class
GenericRevisionControlSystem. 

TODO:
    * move to the translate toolkit and split into different files
"""

import re
import os

# use either 'popen2' or 'subprocess' for command execution
try:
    # available for python >= 2.4
    import subprocess

    # The subprocess module allows to use cross-platform command execution
    # without using the shell (increases security).

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


class GenericRevisionControlSystem:
    """The super class for all version control classes.

    Always inherit from this class to implement another RC interface.

    At least the two attributes "RCS_METADIR" and "SCAN_PARENTS" must be 
    overriden by all implementations that derive from this class.

    By default, all implementations can rely on the following attributes:
        root_dir: the parent of the metadata directory of the working copy
        location_abs: the absolute path of the RCS object
        location_rel: the path of the RCS object relative to 'root_dir'
    """

    RCS_METADIR = None
    """The name of the metadata directory of the RCS

    e.g.: for Subversion -> ".svn"
    """

    SCAN_PARENTS = None
    """whether to check the parent directories for the metadata directory of
    the RCS working copy
    
    some revision control systems store their metadata directory only
    in the base of the working copy (e.g. bzr, GIT and Darcs)
    use "True" for these RCS

    other RCS store a metadata directory in every single directory of
    the working copy (e.g. Subversion and CVS)
    use "False" for these RCS
    """

    def __init__(self, location):
        """find the relevant information about this RCS object
        
        The IOError exception indicates that the specified object (file or
        directory) is not controlled by the given version control system.
        """
        # check if the implementation looks ok - otherwise raise IOError
        self._self_check()
        # search for the repository information
        result = self._find_rcs_directory(location)
        if result is None:
            raise IOError("Could not find revision control information: %s" \
                    % location)
        else:
            self.root_dir, self.location_abs, self.location_rel = result

    def _find_rcs_directory(self, rcs_obj):
        """Try to find the metadata directory of the RCS

        returns a tuple:
            the absolute path of the directory, that contains the metadata directory
            the absolute path of the RCS object
            the relative path of the RCS object based on the directory above
        """
        rcs_obj_dir = os.path.dirname(os.path.abspath(rcs_obj))
        if os.path.isdir(os.path.join(rcs_obj_dir, self.RCS_METADIR)):
            # is there a metadir next to the rcs_obj?
            # (for Subversion, CVS, ...)
            location_abs = os.path.abspath(rcs_obj)
            location_rel = os.path.basename(location_abs)
            return (rcs_obj_dir, location_abs, location_rel)
        elif self.SCAN_PARENTS:
            # scan for the metadir in parent directories
            # (for bzr, GIT, Darcs, ...)
            return self._find_rcs_in_parent_directories(rcs_obj)
        else:
            # no RCS metadata found
            return None
    
    def _find_rcs_in_parent_directories(self, rcs_obj):
        """Try to find the metadata directory in all parent directories"""
        # first: resolve possible symlinks
        current_dir = os.path.dirname(os.path.realpath(rcs_obj))
        # prevent infite loops
        max_depth = 64
        # stop as soon as we find the metadata directory
        while not os.path.isdir(os.path.join(current_dir, self.RCS_METADIR)):
            if os.path.dirname(current_dir) == current_dir:
                # we reached the root directory - stop
                return None
            if max_depth <= 0:
                # some kind of dead loop or a _very_ deep directory structure
                return None
            # go to the next higher level
            current_dir = os.path.dirname(current_dir)
        # the loop was finished successfully
        # i.e.: we found the metadata directory
        rcs_dir = current_dir
        location_abs = os.path.realpath(rcs_obj)
        # strip the base directory from the path of the rcs_obj
        basedir = rcs_dir + os.path.sep
        if location_abs.startswith(basedir):
            # remove the base directory (including the trailing slash)
            location_rel = location_abs.replace(basedir, "", 1)
            # successfully finished
            return (rcs_dir, location_abs, location_rel)
        else:
            # this should never happen
            return None
        
    def _self_check(self):
        """Check if all necessary attributes are defined

        Useful to make sure, that a new implementation does not forget
        something like "RCS_METADIR"
        """
        if self.RCS_METADIR is None:
            raise IOError("Incomplete RCS interface implementation: " \
                    + "self.RCS_METADIR is None")
        if self.SCAN_PARENTS is None:
            raise IOError("Incomplete RCS interface implementation: " \
                    + "self.SCAN_PARENTS is None")
        # we do not check for implemented functions - they raise
        # NotImplementedError exceptions anyway
        return True
                    
    def getcleanfile(self, revision=None):
        """Dummy to be overridden by real implementations"""
        raise NotImplementedError("Incomplete RCS interface implementation:" \
                + " 'getcleanfile' is missing")


    def commit(self, revision=None):
        """Dummy to be overridden by real implementations"""
        raise NotImplementedError("Incomplete RCS interface implementation:" \
                + " 'commit' is missing")


    def update(self, revision=None):
        """Dummy to be overridden by real implementations"""
        raise NotImplementedError("Incomplete RCS interface implementation:" \
                + " 'update' is missing")


class CVS(GenericRevisionControlSystem):
    """Class to manage items under revision control of CVS."""

    RCS_METADIR = "CVS"
    SCAN_PARENTS = False

    def _readfile(self, cvsroot, path, revision=None):
        """
        Read a single file from the CVS repository without checking out a full 
        working directory.
        
        @param: cvsroot: the CVSROOT for the repository
        @param path: path to the file relative to cvs root
        @param revision: revision or tag to get (retrieves from HEAD if None)
        """
        command = ["cvs", "-d", cvsroot, "-Q", "co", "-p"]
        if revision:
            command.extend(["-r", revision])
        # the path is the last argument
        command.append(path)
        exitcode, output, error = pipe(command)
        if exitcode != 0:
            raise IOError("[CVS] Could not read '%s' from '%s': %s / %s" % \
                    (path, cvsroot, output, error))
        return output

    def getcleanfile(self, revision=None):
        """Get the content of the file for the given revision"""
        parentdir = os.path.dirname(self.location_abs)
        cvsdir = os.path.join(parentdir, "CVS")
        cvsroot = open(os.path.join(cvsdir, "Root"), "r").read().strip()
        cvspath = open(os.path.join(cvsdir, "Repository"), "r").read().strip()
        cvsfilename = os.path.join(cvspath, os.path.basename(self.location_abs))
        if revision is None:
            cvsentries = open(os.path.join(cvsdir, "Entries"), "r").readlines()
            revision = self._getcvstag(cvsentries)
        if revision == "BASE":
            cvsentries = open(os.path.join(cvsdir, "Entries"), "r").readlines()
            revision = self._getcvsrevision(cvsentries)
        return self._readfile(cvsroot, cvsfilename, revision)

    def update(self, revision=None):
        """Does a clean update of the given path"""
        working_dir = os.path.dirname(self.location_abs)
        filename = os.path.basename(self.location_abs)
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
        command = ["cvs", "-Q", "update", "-C"]
        if revision:
            command.extend(["-r", revision])
        # the filename is the last argument
        command.append(filename)
        exitcode, output, error = pipe(command)
        # restore backup in case of an error - remove backup for success
        try:
            if exitcode != 0:
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
        working_dir = os.path.dirname(self.location_abs)
        filename = os.path.basename(self.location_abs)
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
        command = ["cvs", "-Q", "commit"]
        if message:
            command.extend(["-m", message])
        # the filename is the last argument
        command.append(filename)
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
        filename = os.path.basename(self.location_abs)
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
        filename = os.path.basename(self.location_abs)
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


class SVN(GenericRevisionControlSystem):
    """Class to manage items under revision control of Subversion."""

    RCS_METADIR = ".svn"
    SCAN_PARENTS = False

    def update(self, revision=None):
        """update the working copy - remove local modifications if necessary"""
        # revert the local copy (remove local changes)
        command = ["svn", "revert", self.location_abs]
        exitcode, output_revert, error = pipe(command)
        # any errors?
        if exitcode != 0:
            raise IOError("[SVN] Subversion error running '%s': %s" \
                    % (command, error))
        # update the working copy to the given revision
        command = ["svn", "update"]
        if not revision is None:
            command.extend(["-r", revision])
        # the filename is the last argument
        command.append(self.location_abs)
        exitcode, output_update, error = pipe(command)
        if exitcode != 0:
            raise IOError("[SVN] Subversion error running '%s': %s" \
                    % (command, error))
        return output_revert + output_update

    def commit(self, message=None):
        """commit the file and return the given message if present"""
        command = ["svn", "-q", "--non-interactive", "commit"]
        if message:
            command.extend(["-m", message])
        # the location is the last argument
        command.append(self.location_abs)
        exitcode, output, error = pipe(command)
        if exitcode != 0:
            raise IOError("[SVN] Error running SVN command '%s': %s" % (command, error))
        return output
    
    def getcleanfile(self, revision=None):
        """return the content of the 'head' revision of the file"""
        command = ["svn", "cat"]
        if not revision is None:
            command.extend(["-r", revision])
        # the filename is the last argument
        command.append(self.location_abs)
        exitcode, output, error = pipe(command)
        if exitcode != 0:
            raise IOError("[SVN] Subversion error running '%s': %s" % (command, error))
        return output


class DARCS(GenericRevisionControlSystem):
    """Class to manage items under revision control of darcs."""

    RCS_METADIR = "_darcs"
    SCAN_PARENTS = True
    
    def update(self, revision=None):
        """Does a clean update of the given path

        @param: revision: ignored for darcs
        """
        # revert local changes (avoids conflicts)
        command = ["darcs", "revert", "--repodir", self.root_dir, 
                "-a", self.location_rel]
        exitcode, output_revert, error = pipe(command)
        if exitcode != 0:
            raise IOError("[Darcs] error running '%s': %s" % (command, error))
        # pull new patches
        command = ["darcs", "pull", "--repodir", self.root_dir, "-a"]
        exitcode, output_pull, error = pipe(command)
        if exitcode != 0:
            raise IOError("[Darcs] error running '%s': %s" % (command, error))
        return output_revert + output_pull

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        if message is None:
            message = ""
        # set change message
        command = ["darcs", "record", "-a", "--repodir", self.root_dir,
                "--skip-long-comment", "-m", message, self.location_rel]
        exitcode, output_record, error = pipe(command)
        if exitcode != 0:
            raise IOError("[Darcs] Error running darcs command '%s': %s" \
                    % (command, error))
        # push changes
        command = ["darcs", "push", "-a", "--repodir", self.root_dir]
        exitcode, output_push, error = pipe(command)
        if exitcode != 0:
            raise IOError("[Darcs] Error running darcs command '%s': %s" \
                    % (command, error))
        return output_record + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the darcs repository

        @param: revision: ignored for darcs
        """
        filename = os.path.join(self.root_dir, self.RCS_METADIR, 'pristine',
                self.location_rel)
        try:
            darcs_file = open(filename)
            output = darcs_file.read()
            darcs_file.close()
        except IOError, error:
            raise IOError("[Darcs] error reading original file '%s': %s" % \
                    (filename, error))
        return output

class GIT(GenericRevisionControlSystem):
    """Class to manage items under revision control of git."""

    RCS_METADIR = ".git"
    SCAN_PARENTS = True

    def _get_git_dir(self):
        """git requires the git metadata directory for every operation
        """
        return os.path.join(self.root_dir, self.RCS_METADIR)
    
    def update(self, revision=None):
        """Does a clean update of the given path"""
        # git checkout
        command = ["git", "--git-dir", self._get_git_dir(),
                "checkout", self.location_rel]
        exitcode, output_checkout, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] checkout failed (%s): %s" % (command, error))
        # pull changes
        command = ["git", "--git-dir", self._get_git_dir(), "pull"]
        exitcode, output_pull, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] pull failed (%s): %s" % (command, error))
        return output_checkout + output_pull

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        # add the file
        command = ["git", "--git-dir", self._get_git_dir(),
                "add", self.location_rel]
        exitcode, output_add, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] add of ('%s', '%s') failed: %s" \
                    % (self.root_dir, self.location_rel, error))
        # commit file
        command = ["git", "--git-dir", self._get_git_dir(), "commit"]
        if message:
            command.extend(["-m", message])
        exitcode, output_commit, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] commit of ('%s', '%s') failed: %s" \
                    % (self.root_dir, self.location_rel, error))
        # push changes
        command = ["git", "--git-dir", self._get_git_dir(), "push"]
        exitcode, output_push, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] push of ('%s', '%s') failed: %s" \
                    % (self.root_dir, self.location_rel, error))
        return output_add + output_commit + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the git repository"""
        # run git-show
        command = ["git", "--git-dir", self._get_git_dir(), "show",
                "HEAD:%s" % self.location_rel]
        exitcode, output, error = pipe(command)
        if exitcode != 0:
            raise IOError("[GIT] 'show' failed for ('%s', %s): %s" \
                    % (self.root_dir, self.location_rel, error))
        return output

class BZR(GenericRevisionControlSystem):
    """Class to manage items under revision control of bzr."""

    RCS_METADIR = ".bzr"
    SCAN_PARENTS = True
    
    def update(self, revision=None):
        """Does a clean update of the given path"""
        # bzr revert
        command = ["bzr", "revert", self.location_abs]
        exitcode, output_revert, error = pipe(command)
        if exitcode != 0:
            raise IOError("[BZR] revert of '%s' failed: %s" \
                    % (self.location_abs, error))
        # bzr pull
        command = ["bzr", "pull"]
        exitcode, output_pull, error = pipe(command)
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
        exitcode, output_commit, error = pipe(command)
        if exitcode != 0:
            raise IOError("[BZR] commit of '%s' failed: %s" \
                    % (self.location_abs, error))
        # bzr push
        command = ["bzr", "push"]
        exitcode, output_push, error = pipe(command)
        if exitcode != 0:
            raise IOError("[BZR] push of '%s' failed: %s" \
                    % (self.location_abs, error))
        return output_commit + output_push

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the bzr repository"""
        # bzr cat
        command = ["bzr", "cat", self.location_abs]
        exitcode, output, error = pipe(command)
        if exitcode != 0:
            raise IOError("[BZR] cat failed for '%s': %s" \
                    % (self.location_abs, error))
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
        sys.stdout.write("\n\n******** %s ********\n\n" % filename)
        sys.stdout.write(contents)


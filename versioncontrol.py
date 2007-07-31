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
    * avoid to use the shell for executing commands (by using arrays instead of
      strings for popen2)
    * replace shell commands with python functions (e.g. "mv")
    * replace unix-only pieces (e.g.: replace "/" with os.path.sep)
"""

import re
import os
import popen2

def pipe(command):
    """Runs a command and returns the output and the error as a tuple."""
    # p = subprocess.Popen(command, shell=True, close_fds=True,
    #     stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    p = popen2.Popen3(command, True)
    (c_stdin, c_stdout, c_stderr) = (p.tochild, p.fromchild, p.childerr)
    output = c_stdout.read()
    error = c_stderr.read()
    ret = p.wait()
    c_stdout.close()
    c_stderr.close()
    c_stdin.close()
    return output, error

def shellescape(path):
    """Shell-escape any non-alphanumeric characters."""
    return re.sub(r'(\W)', r'\\\1', path)


class GenericVersionControlSystem:
    """The super class for all version control classes."""

    # as long as noone overrides this, the test below always succeeds
    MARKER_DIR = "."

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
        path = shellescape(path)
        if revision:
            command = "cvs -d %s -Q co -p -r%s %s" % (cvsroot, revision, path)
        else:
            command = "cvs -d %s -Q co -p %s" % (cvsroot, path)
        output, error = pipe(command)
        if error.startswith('cvs checkout'):
            raise IOError("Could not read %s from %s: %s" % (path, cvsroot, output))
        elif error.startswith('cvs [checkout aborted]'):
            raise IOError("Could not read %s from %s: %s" % (path, cvsroot, output))
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
        dirname = shellescape(os.path.dirname(self.location))
        filename = shellescape(os.path.basename(self.location))
        basecommand = ""
        if dirname:
            basecommand = "cd %s ; " % dirname
        command = basecommand + "mv %s %s.bak ; " % (filename, filename)
        if revision:
            command += "cvs -Q update -C -r%s %s" % (revision, filename)
        else:
            command += "cvs -Q update -C %s" % (filename)
        output, error = pipe(command)
        if error:
            pipe(basecommand + "mv %s.bak %s" % (filename, filename))
            raise IOError("Error running CVS command '%s': %s" % (command, error))
        pipe(basecommand + "rm %s.bak" % filename)
        return output

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        dirname = shellescape(os.path.dirname(self.location))
        filename = shellescape(os.path.basename(self.location))
        basecommand = ""
        if dirname:
            basecommand = "cd %s ; " % dirname
        if message:
            message = ' -m "%s" ' % message
        elif message is None:
            message = ""
        command = basecommand + "cvs -Q commit %s %s" % (message, filename)
        output, error = pipe(command)
        if error:
            raise IOError("Error running CVS command '%s': %s" % (command, error))
        return output

    def _getcvsrevision(self, cvsentries):
        """returns the revision number the file was checked out with by looking
        in the lines of cvsentries
        """
        filename = os.path.basename(self.location)
        for cvsentry in cvsentries:
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
        path = shellescape(self.location)
        command = "svn revert %s" % path
        # update the working copy to the given revision
        if revision is None:
            command += "; svn update %s" % (path,)
        else:
            command += "; svn update -r%s %s" % (revision, path)
        output, error = pipe(command)
        # any error messages?
        if error:
            raise IOError("Subversion error running '%s': %s" % (command, error))
        return output

    def commit(self, message=None):
        """commit the file and return the given message if present"""
        path = shellescape(self.location)
        if message is None:
            message_param = ""
        else:
            message_param = "-m %s" % shellescape(message)
        command = "svn -q --non-interactive commit %s %s" % \
                (message_param, path)
        output, error = pipe(command)
        if error:
            raise IOError("Error running SVN command '%s': %s" % (command, error))
        return output
    
    def getcleanfile(self, revision=None):
        """return the content of the 'head' revision of the file"""
        path = shellescape(self.location)
        if revision is None:
            command = "svn cat %s" % path
        else:
            command = "svn cat -r %s %s" % (shellescape(revision), path)
        output, error = pipe(command)
        if error:
            raise IOError("Subversion error running '%s': %s" % (command, error))
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
                    raise IOError("Darcs: unexpected path names: '%s' and '%s'" \
                            % (self.darcsdir, basedir))
            if self.location is None:
                # we did not find a '_darcs' directory
                raise IOError(err_msg)
                    
    def update(self, revision=None):
        """Does a clean update of the given path"""
        # TODO: check if 'revert' and 'pull' work without specifying '--repodir'
        command = "darcs revert -a %s ; darcs pull -a" % shellescape(self.location)
        output, error = pipe(command)
        if error:
            raise IOError("darcs error running '%s': %s" % (command, error))
        return output

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        if message is None:
            message = ""
        command = "darcs record -a --skip-long-comment -m '%s' %s; darcs push -a" \
                % (message, shellescape(self.location))
        output, error = pipe(command)
        if error:
            raise IOError("Error running darcs command '%s': %s" % (command, error))
        return output

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the darcs repository"""
        command = "cat _darcs/pristine/%s" % shellescape(self.location)
        output, error = pipe(command)
        if error:
            raise IOError("darcs error running '%s': %s" % (command, error))
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
                    raise IOError("Git: unexpected path names: '%s' and '%s'" \
                            % (self.gitdir, basedir))
            if self.location is None:
                # we did not find a '.git' directory
                raise IOError(err_msg)
                    
    def update(self, revision=None):
        """Does a clean update of the given path"""
        command = "git checkout %s ; git pull" % shellescape(self.location)
        output, error = pipe(command)
        if error:
            raise IOError("git error running '%s': %s" % (command, error))
        return output

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        if message is None:
            message = ""
        command = "git add %s; git commit -m '%s'; git push 2>/dev/null" \
                % (shellescape(self.location), message)
        output, error = pipe(command)
        if error:
            raise IOError("Error running git command '%s': %s" % (command, error))
        return output

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the git repository"""
        command = "git cat-file blob $(git ls-tree HEAD %s|sed 's/.* \([a-f0-9]\{40\}\)\t.*/\1/')" \
			% shellescape(self.location)
        output, error = pipe(command)
        if error:
            raise IOError("git error running '%s': %s" % (command, error))
        return output

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
                    raise IOError("Git: unexpected path names: '%s' and '%s'" \
                            % (self.bzrdir, basedir))
            if self.location is None:
                # we did not find a '.bzr' directory
                raise IOError(err_msg)
                    
    def update(self, revision=None):
        """Does a clean update of the given path"""
        command = "bzr revert %s ; bzr pull" % shellescape(self.location)
        output, error = pipe(command)
        if error:
            raise IOError("bzr error running '%s': %s" % (command, error))
        return output

    def commit(self, message=None):
        """Commits the file and supplies the given commit message if present"""
        if message is None:
            message = ""
        command = "bzr commit -m '%s' %s 2>/dev/null; bzr push 2>/dev/null" \
                % (message, shellescape(self.location))
        output, error = pipe(command)
        if error:
            raise IOError("Error running bzr command '%s': %s" % (command, error))
        return output

    def getcleanfile(self, revision=None):
        """Get a clean version of a file from the bzr repository"""
        command = "bzr cat %s" \
			% shellescape(self.location)
        output, error = pipe(command)
        if error:
            raise IOError("bzr error running '%s': %s" % (command, error))
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


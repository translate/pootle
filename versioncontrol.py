#!/usr/bin/env python
# -*- coding: utf-8 -*-
# 
# Copyright 2004-2006 Zuza Software Foundation
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

"""manages projects and files and translations"""

import re
import os
import popen2

def pipe(command):
  """runs a command and returns the output and the error as a tuple"""
  # p = subprocess.Popen(command, shell=True, close_fds=True,
  #   stdin=subprocess.PIPE, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
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
  """Shell-escape any non-alphanumeric characters"""
  return re.sub(r'(\W)', r'\\\1', path)

def cvsreadfile(cvsroot, path, revision=None):
  """
  Read a single file from the CVS repository without checking out a full working directory
  
  cvsroot: the CVSROOT for the repository
  path: path to the file relative to cvs root
  revision: revision or tag to get (retrieves from HEAD if None)
  """
  path = shellescape(path)
  cvsroot = shellescape(cvsroot)
  if revision:
    revision = shellescape(revision)
    command = "cvs -d %s -Q co -p -r%s %s" % (cvsroot, revision, path)
  else:
    command = "cvs -d %s -Q co -p %s" % (cvsroot, path)

  output, error = pipe(command)

  if error.startswith('cvs checkout'):
    raise IOError("Could not read %s from %s: %s" % (path, cvsroot, output))
  elif error.startswith('cvs [checkout aborted]'):
    raise IOError("Could not read %s from %s: %s" % (path, cvsroot, output))
  return output

def cvsupdatefile(path, revision=None):
  """Does a clean update of the given path"""
  dirname = shellescape(os.path.dirname(path))
  filename = shellescape(os.path.basename(path))
  basecommand = ""
  if dirname:
    basecommand = "cd %s ; " % dirname
  command = basecommand + "mv %s %s.bak ; " % (filename, filename)
  if revision:
    revision = shellescape(revision)
    command += "cvs -Q update -C -r%s %s" % (revision, filename)
  else:
    command += "cvs -Q update -C %s" % (filename)
  output, error = pipe(command)
  if error:
    pipe(basecommand + "mv %s.bak %s" % (filename, filename))
    raise IOError("Error running CVS command '%s': %s" % (command, error))
  pipe(basecommand + "rm %s.bak" % filename)
  return output

def cvscommitfile(path, message=None):
  """Commits the file and supplies the given commit message if present"""
  dirname = shellescape(os.path.dirname(path))
  filename = shellescape(os.path.basename(path))
  basecommand = ""
  if dirname:
    basecommand = "cd %s ; " % dirname
  if message:
    message = ' -m %s ' % shellescape(message)
  elif message is None:
    message = ""
  command = basecommand + "cvs -Q commit %s %s" % (message, filename)
  output, error = pipe(command)
  if error:
    raise IOError("Error running CVS command '%s': %s" % (command, error))

def getcvsrevision(cvsentries, filename):
  """returns the revision number the file was checked out with by looking in the lines of cvsentries"""
  for cvsentry in cvsentries:
    cvsentryparts = cvsentry.split("/")
    if len(cvsentryparts) < 6:
      continue
    if os.path.normcase(cvsentryparts[1]) == os.path.normcase(filename):
      return cvsentryparts[2].strip()
  return None

def getcvstag(cvsentries, filename):
  """returns the sticky tag the file was checked out with by looking in the lines of cvsentries"""
  for cvsentry in cvsentries:
    cvsentryparts = cvsentry.split("/")
    if len(cvsentryparts) < 6:
      continue
    if os.path.normcase(cvsentryparts[1]) == os.path.normcase(filename):
      if cvsentryparts[5].startswith("T"):
        return cvsentryparts[5][1:].strip()
  return None

def svnreadfile(path, revision=None):
  """Get a clean version of a file from the SVN repository"""
  path = shellescape(path)
  if revision:
    revision = shellescape(revision)
    command = "svn cat -r %s %s" % (revision, path)
  else:
    command = "svn cat %s" % path
  output, error = pipe(command)
  if error:
    raise IOError("Subversion error running '%s': %s" % (command, error))
  return output

def svnupdatefile(path, revision=None):
  """Does a clean update of the given path"""
  path = shellescape(path)
  command = "svn revert %s ; " % path
  if revision:
    revision = shellescape(revision)
    command += "svn update -r%s %s" % (revision, path)
  else:
    command += "svn update %s" % (path)
  output, error = pipe(command)
  if error:
    raise IOError("Subversion error running '%s': %s" % (command, error))
  return output

def svncommitfile(path, message=None):
  """Commits the file and supplies the given commit message if present"""
  dirname = shellescape(os.path.dirname(path))
  filename = shellescape(os.path.basename(path))
  basecommand = ""
  if dirname:
    basecommand = "cd %s ; " % dirname
  if message:
    message = ' -m %s ' % shellescape(message)
  elif message is None:
    message = ""
  command = basecommand + "svn -q --non-interactive commit %s %s" % (message, filename)
  output, error = pipe(command)
  if error:
    raise IOError("Error running SVN command '%s': %s" % (command, error))

def hascvs(parentdir):
  cvsdir = os.path.join(parentdir, "CVS")
  return os.path.isdir(cvsdir)

def hassvn(parentdir):
  svndir = os.path.join(parentdir, ".svn")
  return os.path.isdir(svndir)

def hasversioning(parentdir):
  return hascvs(parentdir) or hassvn(parentdir)

def getcleanfile(filename, revision=None):
  parentdir = os.path.dirname(filename)
  if hascvs(parentdir):
    cvsdir = os.path.join(parentdir, "CVS")
    cvsroot = open(os.path.join(cvsdir, "Root"), "r").read().strip()
    cvspath = open(os.path.join(cvsdir, "Repository"), "r").read().strip()
    basename = os.path.basename(filename)
    cvsfilename = os.path.join(cvspath, basename)
    if revision is None:
      cvsentries = open(os.path.join(cvsdir, "Entries"), "r").readlines()
      revision = getcvstag(cvsentries, basename)
    if revision == "BASE":
      cvsentries = open(os.path.join(cvsdir, "Entries"), "r").readlines()
      revision = getcvsrevision(cvsentries, basename)
    return cvsreadfile(cvsroot, cvsfilename, revision)
  if hassvn(parentdir):
    return svnreadfile(filename, revision)
  raise IOError("Could not find version control information")

def updatefile(filename, revision=None):
  parentdir = os.path.dirname(filename)
  if hascvs(parentdir):
    return cvsupdatefile(filename, revision)
  if hassvn(parentdir):
    return svnupdatefile(filename, revision)
  raise IOError("Could not find version control information")

def commitfile(filename, message=None):
  parentdir = os.path.dirname(filename)
  if hascvs(parentdir):
    return cvscommitfile(filename, message)
  if hassvn(parentdir):
    return svncommitfile(filename, message)
  raise IOError("Could not find version control information")
  
if __name__ == "__main__":
  import sys
  filenames = sys.argv[1:]
  for filename in filenames:
    contents = getcleanfile(filename)
    sys.stdout.write(contents)


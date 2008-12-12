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

from translate.storage import factory
from translate.filters import checks
from translate.convert import po2csv
from translate.convert import po2xliff
from translate.convert import xliff2po
from translate.convert import po2ts
from translate.convert import pot2po
from translate.convert import po2oo
from translate.tools import pocompile
from translate.tools import pogrep
from translate.search import match
from translate.search import indexing
from translate.storage import statsdb, base
from Pootle import statistics
from Pootle import pootlefile
from translate.storage import versioncontrol
from jToolkit import timecache
from jToolkit import prefs
import time
import os
import cStringIO
import traceback
import gettext
import subprocess
import datetime
import zipfile

from scripts import hooks

from django.contrib.auth.models import User
from Pootle.pootle_app.models import Suggestion, get_profile, Submission
from Pootle import pan_app

class RightsError(ValueError):
  pass

class Rights404Error(ValueError):
  """Throwing this indicates that the user should not know that
  this page even exists, and hence a 404 should be returned.  This
  is *not* a subclass of RightsError, as a RightsError implies that
  the user should be informed an error has occured, and thus is handled
  completely differently"""
  pass

class InternalAdminSession:
  """A fake session used for doing internal admin jobs"""
  def __init__(self):
    self.username = "internal"
    self.isopen = True

  def localize(self, message):
    return message

  def issiteadmin(self):
    return True

class potimecache(timecache.timecache):
  """Caches pootlefile objects, remembers time, and reverts back to statistics when necessary..."""
  def __init__(self, expiryperiod, project):
    """initialises the cache to keep objects for the given expiryperiod, and point back to the project"""
    timecache.timecache.__init__(self, expiryperiod)
    self.project = project

  def __getitem__(self, key):
    """[] access of items"""
    if key and not dict.__contains__(self, key):
      popath = os.path.join(self.project.podir, key)
      if os.path.exists(popath):
        # update the index to pofiles...
        self.project.scanpofiles()
    return timecache.timecache.__getitem__(self, key)

  def expire(self, pofilename):
    """expires the given pofilename by recreating it (holding only stats)"""
    timestamp, currentfile = dict.__getitem__(self, pofilename)
    if currentfile.pomtime is not None:
      # use the currentfile.pomtime as a timestamp as well, so any modifications will extend its life
      if time.time() - currentfile.pomtime > self.expiryperiod.seconds:
        self.__setitem__(pofilename, pootlefile.pootlefile(self.project, pofilename))

class TranslationProject(object):
  """Manages iterating through the translations in a particular project"""
  fileext = "po"
  index_directory = ".translation_index"

  def __init__(self, languagecode, projectcode, potree, create=False):
    self.languagecode = languagecode
    self.projectcode = projectcode
    self.potree = potree
    self.language = self.potree.languages[languagecode]
    self.project = self.potree.projects[projectcode]
    self.languagename = self.potree.getlanguagename(self.languagecode)
    self.projectname = self.potree.getprojectname(self.projectcode)
    self.projectdescription = self.potree.getprojectdescription(self.projectcode)
    self.pofiles = potimecache(15*60, self)
    self.projectcheckerstyle = self.potree.getprojectcheckerstyle(self.projectcode)
    checkerclasses = [checks.projectcheckers.get(self.projectcheckerstyle, checks.StandardChecker), checks.StandardUnitChecker]
    self.checker = checks.TeeChecker(checkerclasses=checkerclasses, errorhandler=self.filtererrorhandler, languagecode=languagecode)
    self.fileext = self.potree.getprojectlocalfiletype(self.projectcode)
    # terminology matcher
    self.termmatcher = None
    self.termmatchermtime = None
    if create:
      self.converttemplates(InternalAdminSession())
    self.podir = self.potree.getpodir(languagecode, projectcode)
    if self.potree.hasgnufiles(self.podir, self.languagecode) == "gnu":
      self.filestyle = "gnu"
    else:
      self.filestyle = "std"
    self.readprefs()
    self.scanpofiles()
    self._indexing_enabled = True
    self._index_initialized = False
   
  def _get_indexer(self):
    if self._indexing_enabled:
      try:
        indexer = self.make_indexer()
        if not self._index_initialized:
          self.initindex(indexer)
          self._index_initialized = True
        return indexer
      except Exception, e:
        print "Could not intialize indexer for %s in %s: %s" % (self.projectcode, self.languagecode, str(e))
        self._indexing_enabled = False
        return None
    else:
      return None

  indexer = property(_get_indexer)

  def _has_index(self):
    return self._indexing_enabled and (self._index_initialized or self.indexer != None)

  has_index = property(_has_index)

  def readprefs(self):
    """reads the project preferences"""
    self.prefs = prefs.PrefsParser()
    self.prefsfile = os.path.join(self.podir, "pootle-%s-%s.prefs" % (self.projectcode, self.languagecode))
    if not os.path.exists(self.prefsfile):
      prefsfile = open(self.prefsfile, "w")
      prefsfile.write("# Pootle preferences for project %s, language %s\n\n" % (self.projectcode, self.languagecode))
      prefsfile.close()
    self.prefs.parsefile(self.prefsfile)

  def saveprefs(self):
    """saves the project preferences"""
    self.prefs.savefile()

  def getrightnames(self, request):
    """gets the available rights and their localized names"""
    localize = request.localize
    # l10n: Verb
    return [("view", localize("View")),
            ("suggest", localize("Suggest")),
            ("translate", localize("Translate")),
            ("overwrite", localize("Overwrite")),
            # l10n: Verb
            ("review", localize("Review")),
            # l10n: Verb
            ("archive", localize("Archive")),
            # l10n: This refers to generating the binary .mo file
            ("pocompile", localize("Compile PO files")),
            ("assign", localize("Assign")),
            ("admin", localize("Administrate")),
            ("commit", localize("Commit")),
           ]

  def getrights(self, request=None, username=None, usedefaults=True):
    """gets the rights for the given user (name or session, or not-logged-in if username is None)
    if usedefaults is False then None will be returned if no rights are defined (useful for editing rights)"""
    # internal admin sessions have all rights
# TODO: Replace this functionality with Django functionality. The Django super user should
#       use Django's permissions system.
#    if isinstance(session, InternalAdminSession):
#      return [right for right, localizedright in self.getrightnames(session)]
    if request is not None and not request.user.is_anonymous and username is None:
      username = request.user.username
    if username is None:
      username = "nobody"
    #FIXME
    rights = None
    rightstree = getattr(self.prefs, "rights", None)
    if rightstree is not None:
      if rightstree.__hasattr__(username):
        rights = rightstree.__getattr__(username)
      else:
        rights = None
    if rights is None:
      if usedefaults:
        if username == "nobody":
          rights = "view"
        elif rightstree is None:
          if self.languagecode == "en":
            rights = "view, archive, pocompile"
          else:
            rights = self.potree.getdefaultrights()
        else:
          rights = getattr(rightstree, "default", None)
      else:
        return rights
    rights = [right.strip() for right in rights.split(",")]
    if request is not None and request.user.is_superuser:
      if "admin" not in rights:
        rights.append("admin")
    return rights

  def getuserswithinterest(self):
    """returns all the users who registered for this language and project"""

    def usableuser(user):
      if user.username in ["__dummy__", "default", "nobody"]:
        return False
      return self.languagecode in map(lambda l: l.code, getattr(user, "languages", []))

    users = {}
    for user in User.objects.all():
      if usableuser(user):
        # Let's build a nice descriptive name for use in the interface. It will
        # contain both the username and the full name, if available.
        username = getattr(user, "username", None)
        name = getattr(user, "name", None)
        if name:
          description = "%s (%s)" % (name, username)
        else:
          description = username
        setattr(user, "description", description)
        users[username] = user
    return users

  def getuserswithrights(self):
    """gets all users that have rights defined for this project"""

    # FIXME This is a bit of a hack to fix the .prefs tendency to split on
    # periods in usernames; the original idea of just looking at all immediate
    # children of prefs would return "user@domain" if "user@domain.com" were
    # listed.  This follows the trail until it finds a string or a unicode,
    # which should be the rights list

    usernames = []
    for username, node in getattr(self.prefs, "rights", {}).iteritems():
      name = username
      while type(node) != str and type(node) != unicode:
        nextname, node = node.iteritems().next()
        name = name + "." + nextname
      usernames.append(name)
    return usernames

  def setrights(self, username, rights):
    """sets the rights for the given username... (or not-logged-in if username is None)"""
    if username is None: username = "nobody"
    if isinstance(rights, list):
      rights = ", ".join(rights)
    if not hasattr(self.prefs, "rights"):
      self.prefs.rights = prefs.PrefNode(self.prefs, "rights")
    self.prefs.rights.__setattr__(username, rights)
    self.saveprefs()

  def delrights(self, request, username):
    """deletes teh rights for the given username"""
    # l10n: Don't translate "nobody" or "default"
    if username == "nobody" or username == "default":
      # l10n: Don't translate "nobody" or "default"
      raise RightsError(request.localize('You cannot remove the "nobody" or "default" user'))
    self.prefs.rights.__delattr__(username)
    self.saveprefs()

  def getgoalnames(self):
    """gets the goals and associated files for the project"""
    goals = getattr(self.prefs, "goals", {})
    goallist = []
    for goalname, goalnode in goals.iteritems():
      goallist.append(goalname.decode("utf-8"))
    goallist.sort()
    return goallist

  def getgoals(self):
    """gets the goal, goalnode tuples"""
    goals = getattr(self.prefs, "goals", {})
    newgoals = {}
    for goalname, goalnode in goals.iteritems():
      newgoals[goalname.decode("utf-8")] = goalnode
    return newgoals

  def getgoalfiles(self, goalname, dirfilter=None, maxdepth=None, includedirs=True, expanddirs=False, includepartial=False):
    """gets the files for the given goal, with many options!
    dirfilter limits to files in a certain subdirectory
    maxdepth limits to files / directories of a certain depth
    includedirs specifies whether to return directory names
    expanddirs specifies whether to expand directories and return all files in them
    includepartial specifies whether to return directories that are not in the goal, but have files below maxdepth in the goal"""
    if not goalname:
      return self.getnogoalfiles(dirfilter=dirfilter, maxdepth=maxdepth, includedirs=includedirs, expanddirs=expanddirs)
    goals = getattr(self.prefs, "goals", {})
    poext = os.extsep + self.fileext
    pathsep = os.path.sep
    unique = lambda filelist: dict.fromkeys(filelist).keys()
    for testgoalname, goalnode in self.getgoals().iteritems():
      if goalname != testgoalname: continue
      goalmembers = getattr(goalnode, "files", "")
      goalmembers = [goalfile.strip() for goalfile in goalmembers.split(",") if goalfile.strip()]
      goaldirs = [goaldir for goaldir in goalmembers if goaldir.endswith(pathsep)]
      goalfiles = [goalfile for goalfile in goalmembers if not goalfile.endswith(pathsep) and goalfile in self.pofilenames]
      if expanddirs:
        expandgoaldirs = []
        expandgoalfiles = []
        for goaldir in goaldirs:
          expandedfiles = self.browsefiles(dirfilter=goaldir, includedirs=includedirs, includefiles=True)
          expandgoalfiles.extend([expandfile for expandfile in expandedfiles if expandfile.endswith(poext)])
          expandgoaldirs.extend([expanddir + pathsep for expanddir in expandedfiles if not expanddir.endswith(poext)])
        goaldirs = unique(goaldirs + expandgoaldirs)
        goalfiles = unique(goalfiles + expandgoalfiles)
      if dirfilter:
        if not dirfilter.endswith(pathsep) and not dirfilter.endswith(poext):
          dirfilter += pathsep
        goalfiles = [goalfile for goalfile in goalfiles if goalfile.startswith(dirfilter)]
        goaldirs = [goaldir for goaldir in goaldirs if goaldir.startswith(dirfilter)]
      if maxdepth is not None:
        if includepartial:
          partialdirs = [goalfile for goalfile in goalfiles if goalfile.count(pathsep) > maxdepth]
          partialdirs += [goalfile for goalfile in goaldirs if goalfile.count(pathsep) > maxdepth]
          makepartial = lambda goalfile: pathsep.join(goalfile.split(pathsep)[:maxdepth+1])+pathsep
          partialdirs = [makepartial(goalfile) for goalfile in partialdirs]
        goalfiles = [goalfile for goalfile in goalfiles if goalfile.count(pathsep) <= maxdepth]
        goaldirs = [goaldir for goaldir in goaldirs if goaldir.count(pathsep) <= maxdepth+1]
        if includepartial:
          goaldirs += partialdirs
      if includedirs:
        return unique(goalfiles + goaldirs)
      else:
        return unique(goalfiles)
    return []

  def getnogoalfiles(self, dirfilter=None, maxdepth=None, includedirs=True, expanddirs=False):
    """Returns the files that are not in a goal. This works with getgoalfiles
    and therefre the API resembles that closely"""
    all = self.browsefiles(dirfilter=dirfilter, maxdepth=maxdepth, includedirs=includedirs)
    pathsep = os.path.sep
    for testgoalname in self.getgoals():
      goalfiles = self.getgoalfiles(testgoalname, dirfilter=dirfilter, maxdepth=maxdepth, includedirs=includedirs, expanddirs=expanddirs, includepartial=False)
      for goalfile in goalfiles:
        if goalfile.endswith(pathsep):
          goalfile = goalfile[:-len(pathsep)]
        all.remove(goalfile)
    return all

  def getancestry(self, filename):
    """returns parent directories of the file"""
    ancestry = []
    parts = filename.split(os.path.sep)
    for i in range(1, len(parts)):
      ancestor = os.path.join(*parts[:i]) + os.path.sep
      ancestry.append(ancestor)
    return ancestry

  def getfilegoals(self, filename):
    """gets the goals the given file is part of"""
    goals = self.getgoals()
    filegoals = []
    ancestry = self.getancestry(filename)
    for goalname, goalnode in goals.iteritems():
      goalfiles = getattr(goalnode, "files", "")
      goalfiles = [goalfile.strip() for goalfile in goalfiles.split(",") if goalfile.strip()]
      if filename in goalfiles:
        filegoals.append(goalname)
        continue
      for ancestor in ancestry:
        if ancestor in goalfiles:
          filegoals.append(goalname)
          continue
    return filegoals

  def setfilegoals(self, request, goalnames, filename):
    """sets the given file to belong to the given goals exactly"""
    filegoals = self.getfilegoals(filename)
    for othergoalname in filegoals:
      if othergoalname not in goalnames:
        self.removefilefromgoal(request, othergoalname, filename)
    for goalname in goalnames:
      goalfiles = self.getgoalfiles(goalname)
      if filename not in goalfiles:
        goalfiles.append(filename)
        self.setgoalfiles(request, goalname, goalfiles)

  def removefilefromgoal(self, request, goalname, filename):
    """removes the given file from the goal"""
    goalfiles = self.getgoalfiles(goalname)
    if filename in goalfiles:
      goalfiles.remove(filename)
      self.setgoalfiles(request, goalname, goalfiles)
    else:
      unique = lambda filelist: dict.fromkeys(filelist).keys()
      ancestry = self.getancestry(filename)
      for ancestor in ancestry:
        if ancestor in goalfiles:
          filedepth = filename.count(os.path.sep)
          ancestordirs = self.getgoalfiles(goalname, ancestor, maxdepth=filedepth+1, includedirs=True, expanddirs=True)
          ancestordirs = [ancestorfile for ancestorfile in ancestordirs if ancestorfile.endswith(os.path.sep)]
          if filename.endswith(os.path.sep):
            ancestorfiles = self.getgoalfiles(goalname, ancestor, maxdepth=filedepth-1, expanddirs=True)
          else:
            ancestorfiles = self.getgoalfiles(goalname, ancestor, maxdepth=filedepth, expanddirs=True)
          ancestorfiles = unique(ancestordirs + ancestorfiles)
          if not filename in ancestorfiles:
            raise KeyError("expected to find file %s in ancestor %s files %r" % (filename, ancestor, ancestorfiles))
          ancestorfiles.remove(filename)
          ancestorfiles.remove(ancestor)
          goalfiles.remove(ancestor)
          goalfiles.extend(ancestorfiles)
          self.setgoalfiles(request, goalname, goalfiles)
          continue

  def setgoalfiles(self, request, goalname, goalfiles):
    """sets the goalfiles for the given goalname"""
    if "admin" not in self.getrights(request):
      raise RightsError(request.localize("You do not have rights to alter goals here"))
    if isinstance(goalfiles, list):
      goalfiles = [goalfile.strip() for goalfile in goalfiles if goalfile.strip()]
      goalfiles.sort()
      goalfiles = ", ".join(goalfiles)
    if not hasattr(self.prefs, "goals"):
      self.prefs.goals = prefs.PrefNode(self.prefs, "goals")
    goals = self.getgoals()
    goalname = goalname.encode("utf-8")
    if not goalname in goals:
      # TODO: check that its a valid goalname (alphanumeric etc)
      self.prefs.goals.__setattr__(goalname, prefs.PrefNode(self.prefs.goals, goalname))
    goalnode = self.prefs.goals.__getattr__(goalname)
    goalnode.files = goalfiles
    self.saveprefs()

  def getgoalusers(self, goalname):
    """gets the users for the given goal"""
    goals = self.getgoals()
    for testgoalname, goalnode in goals.iteritems():
      if goalname != testgoalname: continue
      goalusers = getattr(goalnode, "users", "")
      goalusers = [goaluser.strip() for goaluser in goalusers.split(",") if goaluser.strip()]
      return goalusers
    return []

  def getusergoals(self, username):
    """gets the goals the given user is part of"""
    goals = getattr(self.prefs, "goals", {})
    usergoals = []
    for goalname, goalnode in goals.iteritems():
      goalusers = getattr(goalnode, "users", "")
      goalusers = [goaluser.strip() for goaluser in goalusers.split(",") if goaluser.strip()]
      if username in goalusers:
        usergoals.append(goalname)
        continue
    return usergoals

  def addusertogoal(self, request, goalname, username, exclusive=False):
    """adds the given user to the goal"""
    if exclusive:
      usergoals = self.getusergoals(username)
      for othergoalname in usergoals:
        if othergoalname != goalname:
          self.removeuserfromgoal(request, othergoalname, username)
    goalusers = self.getgoalusers(goalname)
    if username not in goalusers:
      goalusers.append(username)
      self.setgoalusers(request, goalname, goalusers)

  def removeuserfromgoal(self, request, goalname, username):
    """removes the given user from the goal"""
    goalusers = self.getgoalusers(goalname)
    if username in goalusers:
      goalusers.remove(username)
      self.setgoalusers(request, goalname, goalusers)

  def setgoalusers(self, request, goalname, goalusers):
    """sets the goalusers for the given goalname"""
    if isinstance(goalname, unicode):
      goalname = goalname.encode('utf-8')
    if "admin" not in self.getrights(request):
      raise RightsError(request.localize("You do not have rights to alter goals here"))
    if isinstance(goalusers, list):
      goalusers = [goaluser.strip() for goaluser in goalusers if goaluser.strip()]
      goalusers = ", ".join(goalusers)
    if not hasattr(self.prefs, "goals"):
      self.prefs.goals = prefs.PrefNode(self.prefs, "goals")
    if not hasattr(self.prefs.goals, goalname):
      self.prefs.goals.__setattr__(goalname, prefs.PrefNode(self.prefs.goals, goalname))
    goalnode = self.prefs.goals.__getattr__(goalname)
    goalnode.users = goalusers
    self.saveprefs()

  def scanpofiles(self):
    """sets the list of pofilenames by scanning the project directory"""
    self.pofilenames = self.potree.getpofiles(self.languagecode, self.projectcode, poext=self.fileext)
    filename_set = set(self.pofilenames)
    pootlefile_set = set(self.pofiles.keys())
    # add any files that we don't have yet
    try:
        for filename in filename_set.difference(pootlefile_set):
            self.pofiles[filename] = pootlefile.pootlefile(self, filename)
    except UnicodeDecodeError:
      print "Unicode Error on file %s" % pofilename
      raise

    # remove any files that have been deleted since initialization
    for filename in pootlefile_set.difference(filename_set):
        del self.pofiles[filename]

  def getuploadpath(self, dirname, localfilename):
    """gets the path of a translation file being uploaded securely, creating directories as neccessary"""
    if os.path.isabs(dirname) or dirname.startswith("."):
      raise ValueError("invalid/insecure file path: %s" % dirname)
    if os.path.basename(localfilename) != localfilename or localfilename.startswith("."):
      raise ValueError("invalid/insecure file name: %s" % localfilename)
    if self.filestyle == "gnu":
      if not self.potree.languagematch(self.languagecode, localfilename[:-len("."+self.fileext)]):
        raise ValueError("invalid GNU-style file name %s: must match '%s.%s' or '%s[_-][A-Z]{2,3}.%s'" % (localfilename, self.languagecode, self.fileext, self.languagecode, self.fileext))
    dircheck = self.podir
    for part in dirname.split(os.sep):
      dircheck = os.path.join(dircheck, part)
      if dircheck and not os.path.isdir(dircheck):
        os.mkdir(dircheck)
    return os.path.join(self.podir, dirname, localfilename)

  def uploadfile(self, request, dirname, filename, contents, overwrite=False):
    """uploads an individual file"""
    pathname = self.getuploadpath(dirname, filename)
    for extention in ["xliff", "xlf", "xlff"]:
      if filename.endswith(extention):
        pofilename = filename[:-len(os.extsep+extention)] + os.extsep + self.fileext
        popathname = self.getuploadpath(dirname, pofilename)
        break
    else:
      pofilename = filename
      popathname = pathname

    rights = self.getrights(request)

    if os.path.exists(popathname) and not overwrite:
      origpofile = self.getpofile(os.path.join(dirname, pofilename))
      newfileclass = factory.getclass(pathname)
      infile = cStringIO.StringIO(contents)
      newfile = newfileclass.parsefile(infile)
      if "admin" in rights:
        origpofile.mergefile(newfile, request.user.username)
      elif "translate" in rights:
        origpofile.mergefile(newfile, request.user.username, allownewstrings=False)
      elif "suggest" in rights:
        origpofile.mergefile(newfile, request.user.username, suggestions=True)
      else:
        raise RightsError(request.localize("You do not have rights to upload files here"))
    else:
      if overwrite and not ("admin" in rights or "overwrite" in rights):
        raise RightsError(request.localize("You do not have rights to overwrite files here"))
      elif not os.path.exists(popathname) and not ("admin" in rights or "overwrite" in rights):
        raise RightsError(request.localize("You do not have rights to upload new files here"))
      outfile = open(popathname, "wb")
      outfile.write(contents)
      outfile.close()

  def updatepofile(self, request, dirname, pofilename):
    """updates an individual PO file from version control"""
    if "admin" not in self.getrights(request):
      raise RightsError(request.localize("You do not have rights to update files here"))
    # read from version control
    pathname = self.getuploadpath(dirname, pofilename)
    try:
      pathname = hooks.hook(self.projectcode, "preupdate", pathname)
    except:
      pass

    if os.path.exists(pathname):
      popath = os.path.join(dirname, pofilename)

      currentpofile = self.getpofile(popath)
      # matching current file with BASE version
      # TODO: add some locking here...
      # reading new version of file
      versioncontrol.updatefile(pathname)
      newpofile = pootlefile.pootlefile(self, popath)
      newpofile.pofreshen()
      newpofile.mergefile(currentpofile, "versionmerge")
      self.pofiles[pofilename] = newpofile
    else:
      versioncontrol.updatefile(pathname)

    get_profile(request.user).add_message("Updated file: <em>%s</em>" % pofilename)

    try:
      hooks.hook(self.projectcode, "postupdate", pathname)
    except:
      pass

    if newpofile:
      # Update po index for new file
      self.stats = {}
      for xpofilename in self.pofilenames:
        self.getpostats(xpofilename)
        self.pofiles[xpofilename] = pootlefile.pootlefile(self, xpofilename)
        self.pofiles[xpofilename].statistics.getstats()
        self.updateindex(self.indexer, xpofilename)
      self.projectcache = {}

  def runprojectscript(self, scriptdir, target, extraargs = []):
    currdir = os.getcwd()
    script = os.path.join(scriptdir, self.projectcode)
    try:
      os.chdir(scriptdir)
      cmd = [script, target]
      cmd.extend(extraargs)
      subprocess.call(cmd)
    except:
      pass # If something goes wrong, we just continue without worrying
    os.chdir(currdir)

  def commitpofile(self, request, dirname, pofilename):
    """commits an individual PO file to version control"""
    if "commit" not in self.getrights(request):
      raise RightsError(request.localize("You do not have rights to commit files here"))
    pathname = self.getuploadpath(dirname, pofilename)
    stats = self.getquickstats([os.path.join(dirname, pofilename)])
    statsstring = "%d of %d messages translated (%d fuzzy)." % \
        (stats["translated"], stats["total"], stats["fuzzy"])

    message="Commit from %s by user %s, editing po file %s. %s" % (pan_app.prefs.title, request.user.username, pofilename, statsstring)
    author=request.user.username
    fulldir = os.path.split(pathname)[0]
   
    try:
      filestocommit = hooks.hook(self.projectcode, "precommit", pathname, author=author, message=message)
    except ImportError:
      # Failed to import the hook - we're going to assume there just isn't a hook to
      # import.  That means we'll commit the original file.
      filestocommit = [pathname]

    success = True
    try:
      for file in filestocommit:
        versioncontrol.commitfile(file, message=message, author=author)
        get_profile(request.user).add_message("Committed file: <em>%s</em>" % file)
    except Exception, e:
      print "Failed to commit files: %s" % e
      get_profile(request.user).add_message("Failed to commit file: %s" % e)
      success = False 
    try:
      hooks.hook(self.projectcode, "postcommit", pathname, success=success)
    except:
      pass

  def initialize(self, request, languagecode):
    try:
      projectdir = os.path.join(self.potree.podirectory, self.projectcode)
      hooks.hook(self.projectcode, "initialize", projectdir, languagecode)
      self.scanpofiles()
    except Exception, e:
      print "Failed to initialize (%s): %s" % (languagecode, e)

  def converttemplates(self, request):
    """creates PO files from the templates"""
    projectdir = os.path.join(self.potree.podirectory, self.projectcode)
    if not os.path.exists(projectdir):
      os.mkdir(projectdir)
    templatesdir = os.path.join(projectdir, "templates")
    if not os.path.exists(templatesdir):
      templatesdir = os.path.join(projectdir, "pot")
      if not os.path.exists(templatesdir):
        templatesdir = projectdir
    if self.potree.isgnustyle(self.projectcode):
      self.filestyle = "gnu"
    else:
      self.filestyle = "std"
    templates = self.potree.gettemplates(self.projectcode)
    if self.filestyle == "gnu":
      self.podir = projectdir
      if not templates:
        raise NotImplementedError("Cannot create GNU-style translation project without templates")
    else:
      self.podir = os.path.join(projectdir, self.languagecode)
      if not os.path.exists(self.podir):
        os.mkdir(self.podir)
    for potfilename in templates:
      inputfile = open(os.path.join(templatesdir, potfilename), "rb")
      outputfile = cStringIO.StringIO()
      if self.filestyle == "gnu":
        pofilename = self.languagecode + os.extsep + "po"
      else:
        pofilename = potfilename[:-len(os.extsep+"pot")] + os.extsep + "po"
      origpofilename = os.path.join(self.podir, pofilename)
      if os.path.exists(origpofilename):
        origpofile = open(origpofilename)
      else:
        origpofile = None
        if not os.path.exists(os.path.dirname(origpofilename)):
          os.makedirs(os.path.dirname(origpofilename))
      pot2po.convertpot(inputfile, outputfile, origpofile)
      outfile = open(origpofilename, "wb")
      outfile.write(outputfile.getvalue())
      outfile.close()
      self.scanpofiles()

  def filtererrorhandler(self, functionname, str1, str2, e):
    print "error in filter %s: %r, %r, %s" % (functionname, str1, str2, e)
    return False

  def getarchive(self, pofilenames):
    """returns an archive of the given filenames"""
    try:
      # using zip command line is fast
      from tempfile import mkstemp
      # The temporary file below is opened and immediately closed for security reasons
      fd, tempzipfile = mkstemp(prefix='pootle', suffix='.zip')
      os.close(fd)
      os.system("cd %s ; zip -r - %s > %s" % (self.podir, " ".join(pofilenames), tempzipfile))
      filedata = open(tempzipfile, "r").read()
      if filedata:
        return filedata
    finally:
      if os.path.exists(tempzipfile):
        os.remove(tempzipfile)

    # but if it doesn't work, we can do it from python
    archivecontents = cStringIO.StringIO()
    archive = zipfile.ZipFile(archivecontents, 'w', zipfile.ZIP_DEFLATED)
    for pofilename in pofilenames:
      pofile = self.getpofile(pofilename)
      archive.write(pofile.filename, pofilename)
    archive.close()
    return archivecontents.getvalue()

  def uploadarchive(self, request, dirname, archivecontents):
    """uploads the files inside the archive"""

    def unzip_external(archivecontents):
      from tempfile import mkdtemp, mkstemp
      tempdir = mkdtemp(prefix='pootle')
      tempzipfd, tempzipname = mkstemp(prefix='pootle', suffix='.zip')

      try:
        os.write(tempzipfd, archivecontents)
        os.close(tempzipfd)

        import subprocess
        if subprocess.call(["unzip", tempzipname, "-d", tempdir]):
          raise zipfile.BadZipfile(request.localize("Error while extracting archive"))

        def upload(basedir, path, files):
          for fname in files:
            if not os.path.isfile(os.path.join(path, fname)):
              continue
            if not fname.endswith(os.extsep + self.fileext):
              print "error adding %s: not a %s file" % (fname, os.extsep + self.fileext)
              continue
            fcontents = open(os.path.join(path, fname), 'rb').read()
            self.uploadfile(request, path[len(basedir)+1:], fname, fcontents)
        os.path.walk(tempdir, upload, tempdir)
        return
      finally:
        # Clean up temporary file and directory used in try-block
        import shutil
        os.unlink(tempzipname)
        shutil.rmtree(tempdir)

    def unzip_python(archivecontents):
      archive = zipfile.ZipFile(cStringIO.StringIO(archivecontents), 'r')
      # TODO: find a better way to return errors...
      for filename in archive.namelist():
        if not filename.endswith(os.extsep + self.fileext):
          print "error adding %s: not a %s file" % (filename, os.extsep + self.fileext)
          continue
        contents = archive.read(filename)
        subdirname, pofilename = os.path.dirname(filename), os.path.basename(filename)
        try:
          # TODO: use zipfile info to set the time and date of the file
          self.uploadfile(request, os.path.join(dirname, subdirname), pofilename, contents)
        except ValueError, e:
          print "error adding %s" % filename, e
          continue
      archive.close()

    # First we try to use "unzip" from the system, otherwise fall back to using
    # the slower zipfile module (below)...
    try:
      unzip_external(archivecontents)
    except Exception:
      unzip_python(archivecontents)

  def ootemplate(self):
    """Tests whether this project has an OpenOffice.org template SDF file in
    the templates directory."""
    projectdir = os.path.join(self.potree.podirectory, self.projectcode)
    templatefilename = os.path.join(projectdir, "templates", "en-US.sdf")
    if os.path.exists(templatefilename):
      return templatefilename
    else:
      return None

  def getoo(self):
    """Returns an OpenOffice.org gsi file"""
    #TODO: implement caching
    templateoo = self.ootemplate()
    if templateoo is None:
      return
    outputoo = os.path.join(self.podir, self.languagecode + ".sdf")
    inputdir = os.path.join(self.potree.podirectory, self.projectcode, self.languagecode)
    po2oo.main(["-i%s"%inputdir, "-t%s"%templateoo, "-o%s"%outputoo, "-l%s"%self.languagecode, "--progress=none"])
    return file(os.path.join(self.podir, self.languagecode + ".sdf"), "r").read()

  def browsefiles(self, dirfilter=None, depth=None, maxdepth=None, includedirs=False, includefiles=True):
    """gets a list of pofilenames, optionally filtering with the parent directory"""
    if dirfilter is None:
      pofilenames = self.pofilenames
    else:
      if not dirfilter.endswith(os.path.sep) and not dirfilter.endswith(os.extsep + self.fileext):
        dirfilter += os.path.sep
      pofilenames = [pofilename for pofilename in self.pofilenames if pofilename.startswith(dirfilter)]
    if includedirs:
      podirs = {}
      for pofilename in pofilenames:
        dirname = os.path.dirname(pofilename)
        if not dirname:
          continue
        podirs[dirname] = True
        while dirname:
          dirname = os.path.dirname(dirname)
          if dirname:
            podirs[dirname] = True
      podirs = podirs.keys()
    else:
      podirs = []
    if not includefiles:
      pofilenames = []
    if maxdepth is not None:
      pofilenames = [pofilename for pofilename in pofilenames if pofilename.count(os.path.sep) <= maxdepth]
      podirs = [podir for podir in podirs if podir.count(os.path.sep) <= maxdepth]
    if depth is not None:
      pofilenames = [pofilename for pofilename in pofilenames if pofilename.count(os.path.sep) == depth]
      podirs = [podir for podir in podirs if podir.count(os.path.sep) == depth]
    return pofilenames + podirs

  def iterpofilenames(self, lastpofilename=None, includelast=False):
    """iterates through the pofilenames starting after the given pofilename"""
    if not lastpofilename:
      index = 0
    else:
      index = self.pofilenames.index(lastpofilename)
      if not includelast:
        index += 1
    while index < len(self.pofilenames):
      yield self.pofilenames[index]
      index += 1

  def make_indexer(self):
    """get an indexing object for this project

    Since we do not want to keep the indexing databases open for the lifetime of
    the TranslationProject (it is cached!), it may NOT be part of the Project object,
    but should be used via a short living local variable.
    """
    indexdir = os.path.join(self.podir, self.index_directory)
    index = indexing.get_indexer(indexdir)
    index.set_field_analyzers({
            "pofilename": index.ANALYZER_EXACT,
            "itemno": index.ANALYZER_EXACT,
            "pomtime": index.ANALYZER_EXACT})
    return index

  def initindex(self, indexer):
    """initializes the search index"""
    pofilenames = self.pofiles.keys()
    pofilenames.sort()
    for pofilename in pofilenames:
      self.updateindex(indexer, pofilename, optimize=False)

  def updateindex(self, indexer, pofilename, items=None, optimize=True):
    """updates the index with the contents of pofilename (limit to items if given)

    There are three reasons for calling this function:
      1. creating a new instance of L{TranslationProject} (see L{initindex})
          -> check if the index is up-to-date / rebuild the index if necessary
      2. translating a unit via the web interface
          -> (re)index only the specified unit(s)

    The argument L{items} should be None for 1.

    known problems:
      1. This function should get called, when the po file changes externally.
         The function "pofreshen" in pootlefile.py would be the natural place
         for this. But this causes circular calls between the current (r7514)
         statistics code and "updateindex" leading to indexing database lock
         issues.

         WARNING: You have to stop the pootle server before manually changing
         po files, if you want to keep the index database in sync.

    @param pofilename: absolute filename of the po file
    @type pofilename: str
    @param items: list of unit numbers within the po file OR None (=rebuild all)
    @type items: [int]
    @param optimize: should the indexing database be optimized afterwards
    @type optimize: bool
    """
    if indexer == None:
      return False
    pofile = self.pofiles[pofilename]
    # check if the pomtime in the index == the latest pomtime
    try:
        pomtime = statistics.getmodtime(pofile.filename)
        pofilenamequery = indexer.make_query([("pofilename", pofilename)], True)
        pomtimequery = indexer.make_query([("pomtime", str(pomtime))], True)
        gooditemsquery = indexer.make_query([pofilenamequery, pomtimequery], True)
        gooditemsnum = indexer.get_query_result(gooditemsquery).get_matches_count()
        # if there is at least one up-to-date indexing item, then the po file
        # was not changed externally -> no need to update the database
        if (gooditemsnum > 0) and (not items):
          # nothing to be done
          return
        elif items:
          # Update only specific items - usually single translation via the web
          # interface. All other items should still be up-to-date (even with an
          # older pomtime).
          print "updating", self.languagecode, "index for", pofilename, "items", items
          # delete the relevant items from the database
          itemsquery = indexer.make_query([("itemno", str(itemno)) for itemno in items], False)
          indexer.delete_doc([pofilenamequery, itemsquery])
        else:
          # (items is None)
          # The po file is not indexed - or it was changed externally (see
          # "pofreshen" in pootlefile.py).
          print "updating", self.projectcode, self.languagecode, "index for", pofilename
          # delete all items of this file
          indexer.delete_doc({"pofilename": pofilename})
        pofile.pofreshen()
        if items is None:
          # rebuild the whole index
          items = range(pofile.statistics.getitemslen())
        addlist = []
        for itemno in items:
          unit = pofile.getitem(itemno)
          doc = {"pofilename": pofilename, "pomtime": str(pomtime), "itemno": str(itemno)}
          if unit.hasplural():
              orig = "\n".join(unit.source.strings)
              trans = "\n".join(unit.target.strings)
          else:
              orig = unit.source
              trans = unit.target
          doc["source"] = orig
          doc["target"] = trans
          doc["notes"] = unit.getnotes()
          doc["locations"] = unit.getlocations()
          addlist.append(doc)
        if addlist:
          indexer.begin_transaction()
          try:
            for add_item in addlist:
                indexer.index_document(add_item)
          finally:
            indexer.commit_transaction()
            indexer.flush(optimize=optimize)
    except (base.ParseError, IOError, OSError):
        indexer.delete_doc({"pofilename": pofilename})
        print "Not indexing %s, since it is corrupt" % (pofilename,)

  def matchessearch(self, pofilename, search):
    """returns whether any items in the pofilename match the search (based on collected stats etc)"""
    # wrong file location in a "dirfilter" search?
    if search.dirfilter is not None and not pofilename.startswith(search.dirfilter):
      return False
    # search.assignedto == [None] means assigned to nobody
    if search.assignedto or search.assignedaction:
      if search.assignedto == [None]:
        assigns = self.pofiles[pofilename].getassigns().getunassigned(search.assignedaction)
      else:
        assigns = self.pofiles[pofilename].getassigns().getassigns()
        if search.assignedto is not None:
          if search.assignedto not in assigns:
            return False
          assigns = assigns[search.assignedto]
        else:
          assigns = reduce(lambda x, y: x+y, [userassigns.keys() for userassigns in assigns.values()], [])
        if search.assignedaction is not None:
          if search.assignedaction not in assigns:
            return False
    if search.matchnames:
      postats = self.getpostats(pofilename)
      for name in search.matchnames:
        if postats.get(name):
          return True        
      return False
    return True

  def indexsearch(self, search, returnfields):
    """returns the results from searching the index with the given search"""
    def do_search(indexer):
      searchparts = []
      if search.searchtext:
        # Split the search expression into single words. Otherwise xapian and
        # lucene would interprete the whole string as an "OR" combination of
        # words instead of the desired "AND".
        for word in search.searchtext.split():
          # Generate a list for the query based on the selected fields
          querylist = [(f, word) for f in search.searchfields]
          textquery = indexer.make_query(querylist, False)
          searchparts.append(textquery)
      if search.dirfilter:
        pofilenames = self.browsefiles(dirfilter=search.dirfilter)
        filequery = indexer.make_query([("pofilename", pofilename) for pofilename in pofilenames], False)
        searchparts.append(filequery)
      # TODO: add other search items
      limitedquery = indexer.make_query(searchparts, True)
      return indexer.search(limitedquery, returnfields)

    indexer = self.indexer
    if indexer != None:
      return do_search(indexer)
    else:
      return False

  def searchpofilenames(self, lastpofilename, search, includelast=False):
    """find the next pofilename that has items matching the given search"""
    if lastpofilename and not lastpofilename in self.pofiles:
      # accessing will autoload this file...
      self.pofiles[lastpofilename]
    searchpofilenames = None
    if self.has_index and search.searchtext:
      try:
        # TODO: move this up a level, use index to manage whole search, so we don't do this twice
        hits = self.indexsearch(search, "pofilename")
        # there will be only result for the field "pofilename" - so we just
        # pick the first
        searchpofilenames = dict.fromkeys([hit["pofilename"][0] for hit in hits])
      except:
        print "Could not perform indexed search on %s. Index is corrupt." % lastpofilename
        self._indexing_enabled = False
    for pofilename in self.iterpofilenames(lastpofilename, includelast):
      if searchpofilenames is not None:
        if pofilename not in searchpofilenames:
          continue
      if self.matchessearch(pofilename, search):
        yield pofilename

  def searchpoitems(self, pofilename, lastitem, search):
    """finds the next item matching the given search"""

    def indexed(pofilename, search, lastitem):
      filesearch = search.copy()
      filesearch.dirfilter = pofilename
      hits = self.indexsearch(filesearch, "itemno")
      # there will be only result for the field "itemno" - so we just
      # pick the first
      all_items = (int(doc["itemno"][0]) for doc in hits)
      next_items = (search_item for search_item in all_items if search_item > lastitem)
      try:
        # Since we will call self.searchpoitems (the method in which we are)
        # every time a user clicks the next button, the loop which calls yield
        # on indexed will only need a single value from this generator. So we
        # only return a list with a single item.
        return [min(next_items)]
      except ValueError:
        return []

    def non_indexed(pofilename, search, lastitem):
      # Ask pofile for all the possible items which follow lastitem, based on
      # the criteria in search.
      pofile = self.getpofile(pofilename)
      items = pofile.iteritems(search, lastitem)
      if search.searchtext:
        # We'll get here if the user is searching for a piece of text and if no indexer
        # (such as Xapian or Lucene) is usable. First build a grepper...
        grepfilter = pogrep.GrepFilter(search.searchtext, search.searchfields, ignorecase=True)
        # ...then filter the items using the grepper.
        return (item for item in items if grepfilter.filterunit(pofile.getitem(item)))
      else:
        return items

    def get_items(pofilename, search, lastitem):
      if self.has_index and search.searchtext:
        try:
          # Return an iterator using the indexer if indexing is available and if there is searchtext.
          return indexed(pofilename, search, lastitem)
        except:
          print "Could not perform indexed search on %s. Index is corrupt." % pofilename
          self._indexing_enabled = False
      return non_indexed(pofilename, search, lastitem)

    for pofilename in self.searchpofilenames(pofilename, search, includelast=True):
      for item in get_items(pofilename, search, lastitem):
        yield pofilename, item
      # this must be set to None so that the next call to
      # get_items(self.getpofile(pofilename), search, lastitem) [see just above]
      # will start afresh with the first item in the next pofilename.
      lastitem = None

  def reassignpoitems(self, request, search, assignto, action):
    """reassign all the items matching the search to the assignto user(s) evenly, with the given action"""
    # remove all assignments for the given action
    self.unassignpoitems(request, search, None, action)
    assigncount = self.assignpoitems(request, search, assignto, action)
    return assigncount

  def assignpoitems(self, request, search, assignto, action):
    """assign all the items matching the search to the assignto user(s) evenly, with the given action"""
    if not "assign" in self.getrights(request):
      raise RightsError(request.localize("You do not have rights to alter assignments here"))
    if search.searchtext:
      grepfilter = pogrep.GrepFilter(search.searchtext, None, ignorecase=True)
    if not isinstance(assignto, list):
      assignto = [assignto]
    usercount = len(assignto)
    assigncount = 0
    if not usercount:
      return assigncount
    pofilenames = [pofilename for pofilename in self.searchpofilenames(None, search, includelast=True)]
    wordcounts = [(pofilename, self.getpofile(pofilename).statistics.getquickstats()['totalsourcewords']) for pofilename in pofilenames]
    totalwordcount = sum([wordcount for pofilename, wordcount in wordcounts])

    wordsperuser = totalwordcount / usercount
    print "assigning", totalwordcount, "words to", usercount, "user(s)", wordsperuser, "words per user"
    usernum = 0
    userwords = 0
    for pofilename, wordcount in wordcounts:
      pofile = self.getpofile(pofilename)
      sourcewordcount = pofile.statistics.getunitstats()['sourcewordcount']
      for item in pofile.iteritems(search, None):
        # TODO: move this to iteritems
        if search.searchtext:
          validitem = False
          unit = pofile.getitem(item)
          if grepfilter.filterunit(unit):
            validitem = True
          if not validitem:
            continue
        itemwordcount = sourcewordcount[item]
        #itemwordcount = statsdb.wordcount(str(pofile.getitem(item).source))
        if userwords + itemwordcount > wordsperuser:
          usernum = min(usernum+1, len(assignto)-1)
          userwords = 0
        userwords += itemwordcount
        pofile.getassigns().assignto(item, assignto[usernum], action)
        assigncount += 1
    return assigncount

  def unassignpoitems(self, request, search, assignedto, action=None):
    """unassigns all the items matching the search to the assignedto user"""
    if not "assign" in self.getrights(request):
      raise RightsError(request.localize("You do not have rights to alter assignments here"))
    if search.searchtext:
      grepfilter = pogrep.GrepFilter(search.searchtext, None, ignorecase=True)
    assigncount = 0
    for pofilename in self.searchpofilenames(None, search, includelast=True):
      pofile = self.getpofile(pofilename)
      for item in pofile.iteritems(search, None):
        # TODO: move this to iteritems
        if search.searchtext:
          unit = pofile.getitem(item)
          if grepfilter.filterunit(unit):
            pofile.getassigns().unassign(item, assignedto, action)
            assigncount += 1
        else:
          pofile.getassigns().unassign(item, assignedto, action)
          assigncount += 1
    return assigncount

  def getquickstats(self, pofilenames=None):
    """Gets translated and total stats and wordcounts without doing calculations returning dictionary."""
    if pofilenames is None:
      pofilenames = self.pofilenames
    result =  {"translatedsourcewords": 0, "translated": 0,
               "fuzzysourcewords": 0, "fuzzy": 0,
               "totalsourcewords": 0, "total": 0}
    for stats in (self.pofiles[key].statistics.getquickstats() for key in pofilenames):
      for key in result:
        result[key] += stats[key]
    return result

  def combinestats(self, pofilenames=None):
    """combines translation statistics for the given po files (or all if None given)"""
    if pofilenames is None:
      pofilenames = self.pofilenames
    pofilenames = [pofilename for pofilename in pofilenames
                   if pofilename != None and not os.path.isdir(pofilename)]
    total_stats = self.combine_totals(pofilenames)
    total_stats['units'] = self.combine_unit_stats(pofilenames)
    total_stats['assign'] = self.combineassignstats(pofilenames)
    return total_stats

  def combine_totals(self, pofilenames):
    totalstats = {}
    for pofilename in pofilenames:
      pototals = self.getpototals(pofilename)
      for name, items in pototals.iteritems():
        totalstats[name] = totalstats.get(name, 0) + pototals[name]
    return totalstats

  def combine_unit_stats(self, pofilenames):
    unit_stats = {}
    for pofilename in pofilenames:
      postats = self.getpostats(pofilename)
      for name, items in postats.iteritems():
        unit_stats.setdefault(name, []).extend([(pofilename, item) for item in items])
    return unit_stats

  def combineassignstats(self, pofilenames=None, action=None):
    """combines assign statistics for the given po files (or all if None given)"""
    assign_stats = {}
    for pofilename in pofilenames:
      assignstats = self.getassignstats(pofilename, action)
      for name, items in assignstats.iteritems():
        assign_stats.setdefault(name, []).extend([(pofilename, item) for item in items])
    return assign_stats

  def countwords(self, stats):
    """counts the number of words in the items represented by the stats list"""
    wordcount = 0
    for pofilename, item in stats:
      pofile = self.pofiles[pofilename]
      if 0 <= item < len(pofile.statistics.getunitstats()['sourcewordcount']):
        wordcount += pofile.statistics.getunitstats()['sourcewordcount'][item]
    return wordcount

  def getpomtime(self):
    """returns the modification time of the last modified file in the project"""
    return max([pofile.pomtime for pofile in self.pofiles.values()])
  pomtime = property(getpomtime)

  def track(self, pofilename, item, message):
    """sends a track message to the pofile"""
    self.pofiles[pofilename].track(item, message)

  def gettracks(self, pofilenames=None):
    """calculates translation statistics for the given po files (or all if None given)"""
    alltracks = []
    if pofilenames is None:
      pofilenames = self.pofilenames
    for pofilename in pofilenames:
      if not pofilename or os.path.isdir(pofilename):
        continue
      tracker = self.pofiles[pofilename].tracker
      items = tracker.keys()
      items.sort()
      for item in items:
        alltracks.append("%s item %d: %s" % (pofilename, item, tracker[item]))
    return alltracks

  def getpostats(self, pofilename):
    """calculates translation statistics for the given po file"""
    return self.pofiles[pofilename].statistics.getstats()

  def getpototals(self, pofilename):
    """calculates translation statistics for the given po file"""
    return self.pofiles[pofilename].statistics.getquickstats()

  def getassignstats(self, pofilename, action=None):
    """calculates translation statistics for the given po file (can filter by action if given)"""
    polen = self.getpototals(pofilename).get("total", 0)
    # Temporary code to avoid traceback. Was:
#    polen = len(self.getpostats(pofilename)["total"])
    assigns = self.pofiles[pofilename].getassigns().getassigns()
    assignstats = {}
    for username, userassigns in assigns.iteritems():
      allitems = []
      for assignaction, items in userassigns.iteritems():
        if action is None or assignaction == action:
          allitems += [item for item in items if 0 <= item < polen and item not in allitems]
      if allitems:
        assignstats[username] = allitems
    return assignstats

  def getpofile(self, pofilename, freshen=True):
    """parses the file into a pofile object and stores in self.pofiles"""
    pofile = self.pofiles[pofilename]
    if freshen:
      pofile.pofreshen()
    return pofile

  def getpofilelen(self, pofilename):
    """returns number of items in the given pofilename"""
    pofile = self.getpofile(pofilename)
    return len(pofile.total)

  def getitems(self, pofilename, itemstart, itemstop):
    """returns a set of items from the pofile, converted to original and translation strings"""
    pofile = self.getpofile(pofilename)
    units = [pofile.units[index] for index in pofile.total[max(itemstart,0):itemstop]]
    return units

  def updatetranslation(self, pofilename, item, newvalues, request, suggObj=None):
    """updates a translation with a new value..."""
    if "translate" not in self.getrights(request):
      raise RightsError(request.localize("You do not have rights to change translations here"))
    pofile = self.pofiles[pofilename]
    pofile.pofreshen()
    pofile.track(item, "edited by %s" % request.user.username)
    languageprefs = getattr(self.potree.languages, self.languagecode, None)
    
    source = pofile.getitem(item).getsource()

    s = Submission()
    s.creation_time = datetime.datetime.utcnow()

    s.language = self.language 
    s.project = self.project
    s.filename = pofile.pofilename
    s.source = unicode(source)
    s.trans = unicode(newvalues['target'])

    if not request.user.is_anonymous:
      s.submitter = get_profile(request.user)

    s.fromsuggestion = suggObj
    s.save()

    pofile.updateunit(item, newvalues, request.user, languageprefs)
    self.updateindex(self.indexer, pofilename, [item])

  def suggesttranslation(self, pofilename, item, trans, request):
    """stores a new suggestion for a translation..."""
    if "suggest" not in self.getrights(request):
      raise RightsError(request.localize("You do not have rights to suggest changes here"))
    pofile = self.getpofile(pofilename)
    source = pofile.getitem(item).getsource()

    s = Suggestion()
    s.creation_time = datetime.datetime.utcnow()

    s.language = self.language 
    s.project = self.project
    s.filename = pofile.pofilename
    s.source = unicode(source)
    s.trans = unicode(trans)

    s.review_status = "pending"

    # TODO This is a hack to get around the following issue: When one logs
    # out, the user is set to None (since the session is no longer open),
    # but username remains for this query; if someone POSTSs a suggestion
    # while logging out, it will thus go into the .pending file as one of
    # that person's submissions, but into the database as anonymous.  This
    # fixes it by making it an anonymous suggestion in the file.
    if request.user != None:
      s.suggester = get_profile(request.user)
      uname = request.user.username
    else:
      uname = None
    s.save()

    pofile.track(item, "suggestion made by %s" % uname)
    pofile.addsuggestion(item, trans, uname)

  def getsuggestions(self, pofile, item):
    """find all the suggestions submitted for the given (pofile or pofilename) and item"""
    if isinstance(pofile, (str, unicode)):
      pofilename = pofile
      pofile = self.getpofile(pofilename)
    suggestpos = pofile.getsuggestions(item)
    return suggestpos

  def markSuggestion(self, pofile, item, newtrans, request, suggester, status):
    """Marks the suggestion specified by the parameters with the given status,
    and returns that suggestion object"""
    source = pofile.getitem(item).getsource()
    
    query = Suggestion.objects\
        .filter(language=self.language)\
        .filter(project=self.project)\
        .filter(source=unicode(source))\
        .filter(trans=unicode(newtrans))\
        .filter(review_status="pending")

    user = None
    if suggester != None:
      users = User.objects.filter(username=suggester)
      if users.count() > 0:
        query = query.filter(suggester=users[0])

    if query.count() > 0:
      sugg = query[0]
      # If you want to save rejected suggestions in the database, uncomment the following lines and comment out the delete line
      #sugg.reviewer = session.user
      #sugg.reviewStatus = status
      #sugg.reviewTime = datetime.datetime.utcnow()
      sugg.delete()
      return sugg
    else:
      print "No database entry for suggestion found; database integrity issue detected!"
      return None

  def acceptsuggestion(self, pofile, item, suggitem, newtrans, request):
    """accepts the suggestion into the main pofile"""
    if not "review" in self.getrights(request):
      raise RightsError(request.localize("You do not have rights to review suggestions here"))
    if isinstance(pofile, (str, unicode)):
      pofilename = pofile
      pofile = self.getpofile(pofilename)
    suggester = self.getsuggester(pofile, item, suggitem)

    suggObj = self.markSuggestion(pofile, item, newtrans, request, suggester, "accepted")

    pofile.track(item, "suggestion by %s accepted by %s" % (suggester, request.user.username))
    pofile.deletesuggestion(item, suggitem, newtrans)
    self.updatetranslation(pofilename, item, {"target": newtrans, "fuzzy": False}, request, suggObj)

  
  def getsuggester(self, pofile, item, suggitem):
    """returns who suggested the given item's suggitem if recorded, else None"""
    if isinstance(pofile, (str, unicode)):
      pofilename = pofile
      pofile = self.getpofile(pofilename)
    return pofile.getsuggester(item, suggitem)

  def rejectsuggestion(self, pofile, item, suggitem, newtrans, request):
    """rejects the suggestion and removes it from the pending file"""
    if not "review" in self.getrights(request):
      raise RightsError(request.localize("You do not have rights to review suggestions here"))
    if isinstance(pofile, (str, unicode)):
      pofilename = pofile
      pofile = self.getpofile(pofilename)
    suggester = self.getsuggester(pofile, item, suggitem)

    # Deletes the suggestion from the database
    suggObj = self.markSuggestion(pofile, item, newtrans, request, suggester, "rejected")

    pofile.track(item, "suggestion by %s rejected by %s" % (suggester, request.user.username))

    # Deletes the suggestion from the .pending file
    pofile.deletesuggestion(item, suggitem, newtrans)

  def gettmsuggestions(self, pofile, item):
    """find all the TM suggestions for the given (pofile or pofilename) and item"""
    if isinstance(pofile, (str, unicode)):
      pofilename = pofile
      pofile = self.getpofile(pofilename)
    tmsuggestpos = pofile.gettmsuggestions(item)
    return tmsuggestpos

  def isterminologyproject(self):
    """returns whether this project is the main terminology project for a
    language. Currently it is indicated by the project code 'terminology'"""
    return self.projectcode == "terminology"

  def gettermbase(self):
    """returns this project's terminology store"""
    if self.isterminologyproject():
      if len(self.pofiles) > 0:
        for termfile in self.pofiles.values():
          termfile.pofreshen()
        return self
    else:
      termfilename = "pootle-terminology."+self.fileext
      if termfilename in self.pofiles:
        termfile = self.getpofile(termfilename, freshen=True)
        return termfile
    return None

  def gettermmatcher(self):
    """returns the terminology matcher"""
    termbase = self.gettermbase()
    if termbase:
      newmtime = termbase.pomtime
      if newmtime != self.termmatchermtime:
        self.termmatchermtime = newmtime
        if self.isterminologyproject():
          self.termmatcher = match.terminologymatcher(self.pofiles.values())
        else:
          self.termmatcher = match.terminologymatcher(termbase)
    elif not self.isterminologyproject() and self.potree.hasproject(self.languagecode, "terminology"):
      termproject = self.potree.getproject(self.languagecode, "terminology")
      self.termmatcher = termproject.gettermmatcher()
      self.termmatchermtime = termproject.termmatchermtime
    else:
      self.termmatcher = None
      self.termmatchermtime = None
    return self.termmatcher

  def getterminology(self, request, pofile, item):
    """find all the terminology for the given (pofile or pofilename) and item"""
    try:
      termmatcher = self.gettermmatcher()
      if not termmatcher:
        return []
      if isinstance(pofile, (str, unicode)):
        pofilename = pofile
        pofile = self.getpofile(pofilename)
        return termmatcher.matches(pofile.getitem(item).source)
    except Exception, e:
      #TODO: Reimplement this
      #request.server.errorhandler.logerror(traceback.format_exc())
      return []

  def savepofile(self, pofilename):
    """saves changes to disk"""
    pofile = self.getpofile(pofilename)
    pofile.savepofile()

  def getoutput(self, pofilename):
    """returns pofile source"""
    pofile = self.getpofile(pofilename)
    return pofile.getoutput()

  def convert(self, pofilename, destformat):
    """converts the pofile to the given format, returning (etag_if_filepath, filepath_or_contents)"""
    pofile = self.getpofile(pofilename, freshen=False)
    destfilename = pofile.filename[:-len(self.fileext)] + destformat
    destmtime = statistics.getmodtime(destfilename)
    pomtime = statistics.getmodtime(pofile.filename)
    if pomtime and destmtime == pomtime:
      try:
        return pomtime, destfilename
      except Exception, e:
        print "error reading cached converted file %s: %s" % (destfilename, e)
    pofile.pofreshen()
    converters = {"csv": po2csv.po2csv, "xlf": po2xliff.po2xliff, "po": xliff2po.xliff2po, "ts": po2ts.po2ts, "mo": pocompile.POCompile}
    converterclass = converters.get(destformat, None)
    if converterclass is None:
      raise ValueError("No converter available for %s" % destfilename)
    contents = converterclass().convertstore(pofile)
    if not isinstance(contents, basestring):
      contents = str(contents)
    try:
      destfile = open(destfilename, "w")
      destfile.write(contents)
      destfile.close()
      currenttime, modtime = time.time(), pofile.pomtime
      os.utime(destfilename, (currenttime, modtime))
      return modtime, destfilename
    except Exception, e:
      print "error caching converted file %s: %s" % (destfilename, e)
    return False, contents

  def gettext(self, message):
    """uses the project as a live translator for the given message"""
    for pofilename, pofile in self.pofiles.iteritems():
      if pofile.pomtime != statistics.getmodtime(pofile.filename):
        pofile.readpofile()
        pofile.makeindex()
      elif not hasattr(pofile, "sourceindex"):
        pofile.makeindex()
      unit = pofile.sourceindex.get(message, None)
      if not unit or not unit.istranslated():
        continue
      tmsg = unit.target
      if tmsg is not None:
        return tmsg
    return message

  def ugettext(self, message):
    """gets the translation of the message by searching through all the pofiles (unicode version)"""
    for pofilename, pofile in self.pofiles.iteritems():
      try:
        if pofile.pofreshen() or not hasattr(pofile, "sourceindex"):
          pofile.makeindex()
        unit = pofile.sourceindex.get(message, None)
        if not unit or not unit.istranslated():
          continue
        tmsg = unit.target
        if tmsg is not None:
          if isinstance(tmsg, unicode):
            return tmsg
          else:
            return unicode(tmsg, pofile.encoding)
      except Exception, e:
        print "error reading translation from pofile %s: %s" % (pofilename, e)
    return unicode(message)

  def ungettext(self, singular, plural, n):
    """gets the plural translation of the message by searching through all the pofiles (unicode version)"""
    for pofilename, pofile in self.pofiles.iteritems():
      try:
        if pofile.pomtime != statistics.getmodtime(pofile.filename):
          pofile.readpofile()
          pofile.makeindex()
        elif not hasattr(pofile, "sourceindex"):
          pofile.makeindex()
        nplural, pluralequation = pofile.getheaderplural()
        if pluralequation:
          pluralfn = gettext.c2py(pluralequation)
          unit = pofile.sourceindex.get(singular, None)
          if not unit or not unit.istranslated():
            continue
          tmsg = unit.target.strings[pluralfn(n)]
          if tmsg is not None:
            if isinstance(tmsg, unicode):
              return tmsg
            else:
              return unicode(tmsg, pofile.encoding)
      except Exception, e:
        print "error reading translation from pofile %s: %s" % (pofilename, e)
    if n == 1:
      return unicode(singular)
    else:
      return unicode(plural)

  def hascreatemofiles(self, projectcode):
    """returns whether the project has createmofile set"""
    return self.potree.getprojectcreatemofiles(projectcode) == 1

class DummyProject(TranslationProject):
  """a project that is just being used for handling pootlefiles"""
  def __init__(self, podir, checker=None, projectcode=None, languagecode=None):
    """initializes the project with the given podir"""
    self.podir = podir
    if checker is None:
      self.checker = checks.TeeChecker()
    else:
      self.checker = checker
    self.projectcode = projectcode
    self.languagecode = languagecode

  def scanpofiles(self):
    """A null operation if potree is not present"""
    pass

class DummyStatsProject(DummyProject):
  """a project that is just being used for refresh of statistics"""
  def __init__(self, podir, checker, projectcode=None, languagecode=None):
    """initializes the project with the given podir"""
    DummyProject.__init__(self, podir, checker, projectcode, languagecode)

class TemplatesProject(TranslationProject):
  """Manages Template files (.pot files) for a project"""
  fileext = "pot"
  def __init__(self, projectcode, potree):
    super(TemplatesProject, self).__init__("templates", projectcode, potree, create=False)

  def getrights(self, request=None, username=None, usedefaults=True):
    """gets the rights for the given user (name or session, or not-logged-in if username is None)"""
    # internal admin sessions have all rights
    # We don't send the usedefaults parameter through, because we don't want users of this method to
    # change the default behaviour in a template project. Yes, I know: ignorance and deceit.
    rights = super(TemplatesProject, self).getrights(request=request, username=username)
    if rights is not None:
      rights = [right for right in rights if right not in ["translate", "suggest", "pocompile"]]
    return rights


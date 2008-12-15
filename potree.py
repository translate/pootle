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

"""manages the whole set of projects and languages for a pootle installation"""

from Pootle import projects
from Pootle import pootlefile
from Pootle import pagelayout
from translate.misc import autoencode
from translate.lang import data as langdata

import os
from Pootle.pootle_app.models import Language, Project
from Pootle.misc import prefs
from Pootle import pan_app
from django.conf import settings

class POTree:
  """Manages the tree of projects and languages"""
  def __init__(self, server):
    self.server = server

    langlist = Language.objects.order_by('code')
    self.languages = dict( (l.code, l) for l in langlist)

    if not self.haslanguage("templates"):
      newlang = Language(code="templates", fullname=u"Templates")
      newlang.save()
      self.languages[newlang.code] = newlang 
      self.saveprefs()

    projlist = Project.objects.order_by('code')
    self.projects = dict( (p.code, p) for p in projlist) 

    self.podirectory = settings.PODIRECTORY #pan_app.prefs.podirectory
    self.projectcache = {}

  def saveprefs(self):
    """saves any changes made to the preferences"""
    # sqlalchemy autocommit should take care of this
    pass

  def changelanguages(self, argdict):
    """changes language entries"""
    for key, value in argdict.iteritems():
      if key.startswith("languageremove-"):
        languagecode = key.replace("languageremove-", "", 1)
        if self.haslanguage(languagecode):
          langobject = self.languages[languagecode] 
          langobject.delete()
          del self.languages[languagecode]
      elif key.startswith("languagename-"):
        languagecode = key.replace("languagename-", "", 1)
        if self.haslanguage(languagecode):
          languagename = self.getlanguagename(languagecode)
          if languagename != value:
            self.setlanguagename(languagecode, value)
      elif key.startswith("languagespecialchars-"):
        languagecode = key.replace("languagespecialchars-", "", 1)
        if self.haslanguage(languagecode):
          languagespecialchars = self.getlanguagespecialchars(languagecode)
          if languagespecialchars != value:
            self.setlanguagespecialchars(languagecode, value)
      elif key.startswith("languagenplurals-"):
        languagecode = key.replace("languagenplurals-", "", 1)
        if self.haslanguage(languagecode):
          languagenplurals = self.getlanguagenplurals(languagecode)
          if languagenplurals != value:
            self.setlanguagenplurals(languagecode, value)
      elif key.startswith("languagepluralequation-"):
        languagecode = key.replace("languagepluralequation-", "", 1)
        if self.haslanguage(languagecode):
          languagepluralequation = self.getlanguagepluralequation(languagecode)
          if languagepluralequation != value:
            self.setlanguagepluralequation(languagecode, value)
      elif key == "newlanguagecode":
        languagecode = value.lower()
        if not languagecode.strip():
          continue
        if not languagecode.isalpha():
          languagecode = pagelayout.localelanguage(languagecode)
          if languagecode.find("_") >= 0:
            for part in languagecode.split("_"):
              if not part.isalpha():
                raise ValueError("Language code must be alphabetic")
            languagecode, countrycode = languagecode.split("_")
            countrycode = countrycode.upper()
            languagecode = "%s_%s" % (languagecode, countrycode)
          else:
            raise ValueError("Language code must be alphabetic")
        if self.haslanguage(languagecode):
          raise ValueError("Already have language with the code %s" % languagecode)
        languagename = argdict.get("newlanguagename", languagecode)
        languagespecialchars = argdict.get("newlanguagespecialchars", "")
        languagenplurals = argdict.get("newlanguagenplurals", "")
        languagepluralequation = argdict.get("newlanguagepluralequation", "")
        # FIXME need to check that default values are not present
        # if languagename == self.localize("(add language here)"):
        #   raise ValueError("Please set a value for the language name")
        if not languagenplurals.isdigit() and not languagenplurals == "":
          raise ValueError("Number of plural forms must be numeric")
        # if languagenplurals == self.localize("(number of plurals)"):
        #   raise ValueError("Please set a value for the number of plural forms")
        # if languagepluralequation == self.localize("(plural equation)"):
        #   raise ValueError("Please set a value for the plural equation")
        if not languagenplurals == "" and languagepluralequation == "":
          raise ValueError("Please set both the number of plurals and the plural equation OR leave both blank")
        newlang = Language(code=languagecode, fullname=languagename, nplurals=languagenplurals, 
                           pluralequation=languagepluralequation, specialchars=languagespecialchars)
        self.languages[newlang.code] = newlang
        newlang.save()
    self.saveprefs()

  def changeprojects(self, argdict):
    """changes project entries"""
    #Let's reset all "createmofiles" to 0, otherwise we can't disable one
    #since the key will never arrive
    for project in self.getprojectcodes():
      self.setprojectcreatemofiles(project, 0)
    for key, value in argdict.iteritems():
      if key.startswith("projectremove-"):
        projectcode = key.replace("projectremove-", "", 1)
        if self.hasprojectcode(projectcode):
          pobject = self.projects[projectcode] 
          pobject.delete()
          del self.projects[projectcode]
      elif key.startswith("projectname-"):
        projectcode = key.replace("projectname-", "", 1)
        if self.hasprojectcode(projectcode):
          projectname = self.getprojectname(projectcode)
          if projectname != value:
            self.setprojectname(projectcode, value)
      elif key.startswith("projectdescription-"):
        projectcode = key.replace("projectdescription-", "", 1)
        if self.hasprojectcode(projectcode):
          projectdescription = self.getprojectdescription(projectcode)
          if projectdescription != value:
            self.setprojectdescription(projectcode, value)
      elif key.startswith("projectignoredfiles-"):
        projectcode = key.replace("projectignoredfiles-", "", 1)
        if self.hasprojectcode(projectcode):
          projectignoredfiles = self.getprojectignoredfiles(projectcode)
          if projectignoredfiles != value:
            self.setprojectignoredfiles(projectcode, value)
      elif key.startswith("projectcheckerstyle-"):
        projectcode = key.replace("projectcheckerstyle-", "", 1)
        if self.hasprojectcode(projectcode):
          projectcheckerstyle = self.getprojectcheckerstyle(projectcode)
          if projectcheckerstyle != value:
            self.setprojectcheckerstyle(projectcode, value)
      elif key.startswith("projectfiletype-"):
        projectcode = key.replace("projectfiletype-", "", 1)
        if self.hasprojectcode(projectcode):
          projectlocalfiletype = self.getprojectlocalfiletype(projectcode)
          if projectlocalfiletype != value:
            self.setprojectlocalfiletype(projectcode, value)
      elif key.startswith("projectcreatemofiles-"):
        projectcode = key.replace("projectcreatemofiles-", "", 1)
        if self.hasprojectcode(projectcode):
          self.setprojectcreatemofiles(projectcode, 1)
      elif key == "newprojectcode":
        projectcode = value.lower()
        if not projectcode:
          continue
        if not (projectcode[:1].isalpha() and projectcode.replace("_","").isalnum()):
          raise ValueError("Project code must be alphanumeric and start with an alphabetic character (got %r)" % projectcode)
        if self.hasprojectcode(projectcode):
          raise ValueError("Already have project with the code %s" % projectcode)
        projectname = argdict.get("newprojectname", projectcode)
        projecttype = argdict.get("newprojectfiletype", "")
        projectdescription = argdict.get("newprojectdescription", "")
        projectcheckerstyle = argdict.get("newprojectcheckerstyle", "")
        projectcreatemofiles = bool(argdict.get("newprojectcreatemofiles", "") or 0)
        newproject = Project(code=projectcode, fullname=projectname, description=projectdescription, 
                             checkstyle=projectcheckerstyle, localfiletype=projecttype, 
                             createmofiles=projectcreatemofiles)
        self.projects[newproject.code] = newproject
        newproject.save()
        projectdir = os.path.join(self.podirectory, projectcode)
        if not os.path.isdir(projectdir):
          os.mkdir(projectdir)
    self.saveprefs()

  def haslanguage(self, languagecode):
    """checks if this language exists"""
    return languagecode in self.languages.keys() 

  def hasprojectcode(self, projectcode):
    """checks if this project exists"""
    return projectcode in self.projects.keys()

  def getlanguageprefs(self, languagecode):
    """returns the language object"""
    return self.languages[languagecode]

  def getlanguagename(self, languagecode):
    """returns the language's full name"""
    return getattr(self.getlanguageprefs(languagecode), "fullname", languagecode)

  def setlanguagename(self, languagecode, languagename):
    """stes the language's full name"""
    setattr(self.getlanguageprefs(languagecode), "fullname", languagename)

  def getlanguagespecialchars(self, languagecode):
    """returns the language's special characters"""
    return autoencode.autoencode(getattr(self.getlanguageprefs(languagecode), "specialchars", ""), "utf-8")

  def setlanguagespecialchars(self, languagecode, languagespecialchars):
    """sets the language's special characters"""
    setattr(self.getlanguageprefs(languagecode), "specialchars", languagespecialchars)

  def getlanguagenplurals(self, languagecode):
    """returns the language's number of plural forms"""
    return getattr(self.getlanguageprefs(languagecode), "nplurals", "")

  def setlanguagenplurals(self, languagecode, languagenplurals):
    """sets the language's number of plural forms"""
    setattr(self.getlanguageprefs(languagecode), "nplurals", languagenplurals)

  def getlanguagepluralequation(self, languagecode):
    """returns the language's number of plural forms"""
    return getattr(self.getlanguageprefs(languagecode), "pluralequation", "")

  def setlanguagepluralequation(self, languagecode, languagepluralequation):
    """sets the language's number of plural forms"""
    setattr(self.getlanguageprefs(languagecode), "pluralequation", languagepluralequation)

  def getlanguagecodes(self, projectcode=None):
    """returns a list of valid languagecodes for a given project or all projects"""
    alllanguagecodes = self.languages.keys() 
    if projectcode is None:
      languagecodes = alllanguagecodes
    else:
      projectdir = os.path.join(self.podirectory, projectcode)
      if not os.path.exists(projectdir):
        return []
      if self.isgnustyle(projectcode):
        languagecodes = [languagecode for languagecode in alllanguagecodes if self.hasproject(languagecode, projectcode)]
      else:
        subdirs = [fn for fn in os.listdir(projectdir) if os.path.isdir(os.path.join(projectdir, fn))]
        languagecodes = []
        for potentialcode in subdirs:
          if not self.languagematch(None, potentialcode):
            continue
          if potentialcode in alllanguagecodes:
            languagecodes.append(potentialcode)
            continue
          if "-" in potentialcode:
            potentialcode = potentialcode[:potentialcode.find("-")]
          elif "_" in potentialcode:
            potentialcode = potentialcode[:potentialcode.find("_")]
          if potentialcode in alllanguagecodes:
            languagecodes.append(potentialcode)
    languagecodes.sort()
    return languagecodes

  def getlanguages(self, projectcode=None, sortbyname=True):
    """gets a list of (languagecode, languagename) tuples"""
    languagecodes = self.getlanguagecodes(projectcode)
    if sortbyname:
      languages = [(self.getlanguagename(languagecode), languagecode) for languagecode in languagecodes]
      languages.sort()
      return [(languagecode, languagename) for languagename, languagecode in languages]
    else:
      return [(languagecode, self.getlanguagename(languagecode)) for languagecode in languagecodes]

  def getprojectcodes(self, languagecode=None):
    """returns a list of project codes that are valid for the given languagecode or all projects"""
    projectcodes = self.projects.keys() 
    projectcodes.sort()
    if languagecode is None:
      return projectcodes
    else:
      return [projectcode for projectcode in projectcodes if self.hasproject(languagecode, projectcode)]

  def hasproject(self, languagecode, projectcode):
    """returns whether the project exists for the language"""
    if not self.hasprojectcode(projectcode):
      return False
    if languagecode is None:
      return True
    if not self.haslanguage(languagecode):
      return False
    try:
      self.getpodir(languagecode, projectcode)
      return True
    except IndexError:
      return False

  def gettemplates(self, projectcode):
    """returns templates for the given project"""
    projectdir = os.path.join(self.podirectory, projectcode)
    templatesdir = os.path.join(projectdir, "templates")
    if not os.path.exists(templatesdir):
      templatesdir = os.path.join(projectdir, "pot")
      if not os.path.exists(templatesdir):
        templatesdir = projectdir
    potfilenames = []
    def addfiles(podir, dirname, fnames):
      """adds the files to the set of files for this project"""
      basedirname = dirname.replace(podir, "", 1)
      while basedirname.startswith(os.sep):
        basedirname = basedirname.replace(os.sep, "", 1)
      ponames = [fname for fname in fnames if fname.endswith(os.extsep+"pot")]
      potfilenames.extend([os.path.join(basedirname, poname) for poname in ponames])
    os.path.walk(templatesdir, addfiles, templatesdir)
    return potfilenames

  def getproject(self, languagecode, projectcode):
    """returns the project object for the languagecode and projectcode"""
    if (languagecode, projectcode) not in self.projectcache:
      if languagecode == "templates":
        self.projectcache[languagecode, projectcode] = projects.TemplatesProject(projectcode, self)
      else:
        self.projectcache[languagecode, projectcode] = projects.TranslationProject(languagecode, projectcode, self)
    return self.projectcache[languagecode, projectcode]

  def isgnustyle(self, projectcode):
    """checks whether the whole project is a GNU-style project"""
    projectdir = os.path.join(self.podirectory, projectcode)
    return self.hasgnufiles(projectdir)

  def addtranslationproject(self, languagecode, projectcode):
    """creates a new TranslationProject"""
    if self.hasproject(languagecode, projectcode):
      raise ValueError("projects.TranslationProject for project %s, language %s already exists" % (projectcode, languagecode))
    self.projectcache[languagecode, projectcode] = projects.TranslationProject(languagecode, projectcode, self, create=True)

  def getprojectprefs(self, projectcode):
    """returns the project object"""
    return self.projects[projectcode] 

  def getprojectname(self, projectcode):
    """returns the full name of the project"""
    projectprefs = self.getprojectprefs(projectcode)
    return getattr(projectprefs, "fullname", projectcode)

  def setprojectname(self, projectcode, projectname):
    """returns the full name of the project"""
    projectprefs = self.getprojectprefs(projectcode)
    setattr(projectprefs, "fullname", projectname)

  def getprojectdescription(self, projectcode):
    """returns the project description"""
    projectprefs = self.getprojectprefs(projectcode)
    return getattr(projectprefs, "description", projectcode)

  def setprojectdescription(self, projectcode, projectdescription):
    """returns the project description"""
    projectprefs = self.getprojectprefs(projectcode)
    setattr(projectprefs, "description", projectdescription)

  def getprojectlocalfiletype(self, projectcode):
    """returns the project allowed file type. We assume it is .po if nothing
    else is specified."""
    projectprefs = self.getprojectprefs(projectcode)
    type = getattr(projectprefs, "localfiletype", "po")
    if not type:
      type = "po"
    return type

  def setprojectlocalfiletype(self, projectcode, projectfiletype):
    """sets the allowed file type for the project"""
    projectprefs = self.getprojectprefs(projectcode)
    setattr(projectprefs, "localfiletype", projectfiletype)

  def getprojectcheckerstyle(self, projectcode):
    """returns the project checker style"""
    projectprefs = self.getprojectprefs(projectcode)
    return getattr(projectprefs, "checkerstyle", projectcode)

  def setprojectcheckerstyle(self, projectcode, projectcheckerstyle):
    """sets the project checker style"""
    projectprefs = self.getprojectprefs(projectcode)
    setattr(projectprefs, "checkerstyle", projectcheckerstyle)

  def getprojectignoredfiles(self, projectcode):
    """returns a set of the ignored files for the project.  This is temporary code
    until a real preferences system is in place."""
    projectprefs = self.getprojectprefs(projectcode)
    ignoredfiles = getattr(projectprefs, "ignoredfiles", projectcode)
    if len(ignoredfiles) > 0:
      return set(ignoredfiles.split(','))
    return set([])

  def setprojectignoredfiles(self, projectcode, ignoredfiles):
    "sets the ignored files"
    projectprefs = self.getprojectprefs(projectcode)
    setattr(projectprefs, "ignoredfiles", ignoredfiles)

  def getprojectcreatemofiles(self, projectcode):
    """returns whether the project builds MO files"""
    projectprefs = self.getprojectprefs(projectcode)
    return getattr(projectprefs, "createmofiles", False)

  def setprojectcreatemofiles(self, projectcode, projectcreatemofiles):
    """sets whether the project builds MO files"""
    projectprefs = self.getprojectprefs(projectcode)
    setattr(projectprefs, "createmofiles", projectcreatemofiles)

  def hasgnufiles(self, podir, languagecode=None, depth=0, maxdepth=3, poext="po"):
    """returns whether this directory contains gnu-style PO filenames for the given language"""
    try:
      if (podir.startswith(self.podirectory)):
        def getprojectcode(podir=podir):
          """Get the projectcode using the supplied podir."""
          dirs = podir[len(self.podirectory):].split(os.sep)
          if len(dirs[0]):
            projectcode = dirs[0]
          else:
            projectcode = dirs[1]
          return projectcode
        projectprefs = self.getprojectprefs(projectcode)
        style = getattr(projectprefs, "treestyle")
        if    style == "gnu"    \
           or style == "nongnu":
          return style
        else:
          print "Unsupported treestyle value (project %s): %s"%(projectcode,style)
    except:
      pass
    #Let's check to see if we specifically find the correct gnu file
    foundgnufile = False
    if not os.path.isdir(podir):
      return False
    fnames = os.listdir(podir)
    poext = os.extsep + "po"
    subdirs = []
    for fn in fnames:
      if os.path.isdir(os.path.join(podir, fn)):
        # if we have a language subdirectory, we're probably not GNU-style
        if self.languagematch(languagecode, fn):
          return False
        #ignore hidden directories (like index directories)
        if fn[0] == '.':
          continue
        subdirs.append(os.path.join(podir, fn))
      elif fn.endswith(poext):
        if self.languagematch(languagecode, fn[:-len(poext)]):
          foundgnufile = True
        elif not self.languagematch(None, fn[:-len(poext)]):
          return "nongnu"
    if depth < maxdepth:
      for subdir in subdirs:
        style = self.hasgnufiles(subdir, languagecode, depth+1, maxdepth)
        if style == "nongnu":
          return "nongnu"
        if style == "gnu":
          foundgnufile = True

    if foundgnufile:
      return "gnu"
    else:
      return ""

  def getcodesfordir(self, dirname):
    """returns projectcode and languagecode if dirname is a project directory"""
    canonicalpath = lambda path: os.path.normcase(os.path.normpath(os.path.realpath(os.path.abspath(path))))
    dirname = canonicalpath(dirname)
    podirectory = canonicalpath(self.podirectory)
    if dirname == podirectory:
      return "*", None
    for projectcode, projectprefs in self.projects.iteritems():
      projectdir = canonicalpath(os.path.join(self.podirectory, projectcode))
      if projectdir == dirname:
        return projectcode, None
      for languagecode, languageprefs in self.languages.iteritems():
        languagedir = canonicalpath(os.path.join(projectdir, languagecode))
        if not os.path.exists(languagedir):
          languagedirs = [canonicalpath(languagedir) for languagedir in os.listdir(projectdir) if self.languagematch(languagecode, languagedir)]
          if dirname in languagedirs:
            return projectcode, languagecode
        elif languagedir == dirname:
          return projectcode, languagecode
    return None, None

  def getpodir(self, languagecode, projectcode):
    """returns the base directory containing po files for the project"""
    projectdir = os.path.join(self.podirectory, projectcode)
    if not os.path.exists(projectdir):
      raise IndexError("directory not found for project %s" % (projectcode))
    languagedir = os.path.join(projectdir, languagecode)
    if not os.path.exists(languagedir):
      languagedirs = [languagedir for languagedir in os.listdir(projectdir) if self.languagematch(languagecode, languagedir)]
      if not languagedirs:
        # if no matching directories can be found, check if it is a GNU-style project
        if self.hasgnufiles(projectdir, languagecode) == "gnu":
          return projectdir
        raise IndexError("directory not found for language %s, project %s" % (languagecode, projectcode))
      # TODO: handle multiple regions
      if len(languagedirs) > 1:
        raise IndexError("multiple regions defined for language %s, project %s" % (languagecode, projectcode))
      languagedir = os.path.join(projectdir, languagedirs[0])
    return languagedir

  def languagematch(self, languagecode, otherlanguagecode):
    """matches a languagecode to another, ignoring regions in the second"""
    return langdata.languagematch(languagecode, otherlanguagecode)

  def getpofiles(self, languagecode, projectcode, poext="po"):
    """returns a list of po files for the project and language"""
    pofilenames = []
    prefix = os.curdir + os.sep

    def addfiles(podir, dirname, fnames):
      """adds the files to the set of files for this project"""

      # Remove the files we want to ignore
      fnames = set(fnames) - self.getprojectignoredfiles(projectcode)
      
      if dirname == os.curdir:
        basedirname = ""
      else:
        basedirname = dirname.replace(prefix, "", 1)
      for fname in fnames:
        # check that it actually exists (to avoid problems with broken symbolic
        # links, for example)
        fpath = os.path.join(basedirname, fname)
        if fname.endswith(os.extsep+poext):
          pofilenames.append(fpath)

    def addgnufiles(podir, dirname, fnames):
      """adds the files to the set of files for this project"""
      basedirname = dirname.replace(podir, "", 1)
      while basedirname.startswith(os.sep):
        basedirname = basedirname.replace(os.sep, "", 1)
      ext = os.extsep + poext
      ponames = [fn for fn in fnames if fn.endswith(ext) and self.languagematch(languagecode, fn[:-len(ext)])]
      pofilenames.extend([os.path.join(basedirname, poname) for poname in ponames])

    podir = self.getpodir(languagecode, projectcode)
    if self.hasgnufiles(podir, languagecode) == "gnu":
      os.path.walk(podir, addgnufiles, podir)
    else:
      pwd = os.path.abspath(os.curdir)
      os.chdir(podir)
      os.path.walk(os.curdir, addfiles, None)
      os.chdir(pwd)
    return pofilenames

  def getdefaultrights(self):
    """Returns the default rights for a logged in user on this Pootle server."""
    return getattr(pan_app.prefs, "defaultrights", "view, suggest, archive, pocompile")

  def refreshstats(self):
    """manually refreshes (all or missing) the stats files"""
    for projectcode in self.getprojectcodes():
      print "Project %s:" % (projectcode)
      for languagecode in self.getlanguagecodes(projectcode):
        print "Project %s, Language %s:" % (projectcode, languagecode)
        translationproject = self.getproject(languagecode, projectcode)
        translationproject.stats = {}
        for pofilename in translationproject.pofilenames:
          translationproject.indexer # Force indexing to be initialized
          translationproject.getpostats(pofilename)
          translationproject.pofiles[pofilename] = pootlefile.pootlefile(translationproject, pofilename)
          translationproject.pofiles[pofilename].statistics.getstats()
          print ".",
        print
        self.projectcache = {}

class DummyPoTree:
    """A dummy PO tree for testing etc - just treats everything as a single directory"""
    def __init__(self, podir):
        self.podirectory = podir
    def getlanguagename(self, languagecode):
        return languagecode
    def getprojectname(self, projectcode):
        return projectcode
    def getprojectdescription(self, projectcode):
        return projectcode
    def getprojectcheckerstyle(self, projectcode):
        return ""
    def getpodir(self, languagecode, projectcode):
        return self.podirectory
    def hasgnufiles(self, podir, languagecode):
        return False
    def getprojectcreatemofiles(self, projectcode):
        return False
    def getpofiles(self, languagecode, projectcode, poext):
        pofiles = []
        for dirpath, subdirs, filenames in os.walk(self.podirectory, topdown=False):
            if dirpath == self.podirectory:
                subdirpath = ""
            else:
                subdirpath = dirpath.replace(self.podirectory+os.path.sep, "", 1)
            print dirpath, subdirpath, self.podirectory
            pofiles.extend([os.path.join(subdirpath, name) for name in filenames if name.endswith(poext)])
        return pofiles
    def gettemplates(self, projectcode):
        return []
    def languagematch(self, languagecode, filename):
        return True


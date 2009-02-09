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
from pootle_app.core import Language, Project
from Pootle.misc import prefs
from Pootle import pan_app
from django.conf import settings

class POTree:
  """Manages the tree of projects and languages"""
  def __init__(self):
    if not Language.objects.has_templates_project():
      newlang = Language(code="templates", fullname=u"Templates")
      newlang.save()

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

  def refreshstats(self):
    """manually refreshes (all or missing) the stats files"""
    for project in Project.objects.all():
      print "Project %s:" % (project.code)
      for language in Language.objects.all():
        print "Project %s, Language %s:" % (project.code, language.code)
        translationproject = self.getproject(language.code, project.code)
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


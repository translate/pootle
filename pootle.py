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

# TODO: Make this less ugly
import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'Pootle.settings'

# Import this early to force module initialization so that
# our hijacking of Django's translation machinery will work
# from the start.
from Pootle.i18n import gettext

import optparse
from wsgiref.simple_server import make_server
from django.core.handlers.wsgi import WSGIHandler

from jToolkit.web import server
from jToolkit.web import templateserver
from jToolkit.web import session
from jToolkit import prefs
from jToolkit import localize
from jToolkit.widgets import widgets
from jToolkit.widgets import spellui
from jToolkit.widgets import thumbgallery
from jToolkit.web import simplewebserver
from Pootle import indexpage
from Pootle import adminpages
from Pootle import translatepage
from Pootle import pagelayout
from Pootle import projects
from Pootle import pootlefile
from Pootle import users
from Pootle import filelocations
from Pootle import request_cache
from translate.misc import optrecurse
# Versioning information
from Pootle import __version__ as pootleversion
from translate import __version__ as toolkitversion
from jToolkit import __version__ as jtoolkitversion
from Pootle import statistics, pan_app
from Pootle.misc.transaction import django_transaction
from Pootle.misc import prefs, jtoolkit_django
from Pootle.pootle_app.models import Language, Project

try:
  from xml.etree import ElementTree
except ImportError:
  from elementtree import ElementTree
# We don't need kid in this file, but this will show quickly if it is not
# installed. jToolkit won't complain, so we have to stop here if we don't have kid
import kid
import sys
import os
import re
import random
import pprint

def use_request_cache(f):
    def decorated_f(*args, **kwargs):
        try:
            return f(*args, **kwargs)
        finally:
            request_cache.reset()
    return decorated_f

class PootleServer(users.OptionalLoginAppServer):
  """the Server that serves the Pootle Pages"""
  def __init__(self):
    self.potree = pan_app.get_po_tree()
    super(PootleServer, self).__init__()
    self.templatedir = filelocations.templatedir

  def loadurl(self, filename, context):
    """loads a url internally for overlay code"""
    # print "call to load %s with context:\n%s" % (filename, pprint.pformat(context))
    filename = os.path.join(self.templatedir, filename+os.extsep+"html")
    if os.path.exists(filename):
      return open(filename, "r").read()
    return None

  def saveprefs(self):
    """saves any changes made to the preferences"""
    prefs.save_preferences(pan_app.prefs)

  def changeoptions(self, arg_dict):
    """changes options on the instance"""
    prefs.change_preferences(pan_app.prefs, arg_dict)

  def inittranslation(self, localedir=None, localedomains=None, defaultlanguage=None):
    """initializes live translations using the Pootle PO files"""
    self.localedomains = ['jToolkit', 'pootle']
    self.localedir = None
    self.languagelist = self.potree.getlanguagecodes('pootle')
    self.languagenames = self.potree.getlanguages()
    self.defaultlanguage = defaultlanguage
    if self.defaultlanguage is None:
      self.defaultlanguage = getattr(pan_app.prefs, "defaultlanguage", "en")
    if self.potree.hasproject(self.defaultlanguage, 'pootle'):
      try:
        self.translation = self.potree.getproject(self.defaultlanguage, 'pootle')
        return
      except Exception, e:
        self.errorhandler.logerror("Could not initialize translation:\n%s" % str(e))
    # if no translation available, set up a blank translation
    super(PootleServer, self).inittranslation()
    # the inherited method overwrites self.languagenames, so we have to redo it
    self.languagenames = self.potree.getlanguages()

  def gettranslation(self, language):
    """returns a translation object for the given language (or default if language is None)"""
    if language is None:
      return self.translation
    else:
      try:
        return self.potree.getproject(language, 'pootle')
      except Exception, e:
        if not language.startswith('en'):
          self.errorhandler.logerror("Could not get translation for language %r:\n%s" % (language,str(e)))
        return self.translation

  def refreshstats(self, args):
    """refreshes all the available statistics..."""
    if args:
      def filtererrorhandler(functionname, str1, str2, e):
        print "error in filter %s: %r, %r, %s" % (functionname, str1, str2, e)
        return False
      checkerclasses = [projects.checks.StandardChecker, projects.checks.StandardUnitChecker]
      stdchecker = projects.checks.TeeChecker(checkerclasses=checkerclasses, errorhandler=filtererrorhandler)
      for arg in args:
        if not os.path.exists(arg):
          print "file not found:", arg
        if os.path.isdir(arg):
          if not arg.endswith(os.sep):
            arg += os.sep
          projectcode, languagecode = self.potree.getcodesfordir(arg)
          dummyproject = projects.DummyStatsProject(arg, stdchecker, projectcode, languagecode)
          def refreshdir(dummy, dirname, fnames):
            reldirname = dirname.replace(dummyproject.podir, "")
            for fname in fnames:
              fpath = os.path.join(reldirname, fname)
              fullpath = os.path.join(dummyproject.podir, fpath)
              #TODO: PO specific
              if fname.endswith(".po") and not os.path.isdir(fullpath):
                if not os.path.exists(fullpath):
                  print "file does not exist:", fullpath
                  return
                print "refreshing stats for", fpath
                pootlefile.pootlefile(dummyproject, fpath).statistics.updatequickstats()
          os.path.walk(arg, refreshdir, None)
        elif os.path.isfile(arg):
          dummyproject = projects.DummyStatsProject(".", stdchecker)
          print "refreshing stats for", arg
          projects.pootlefile.pootlefile(dummyproject, arg)
    else:
      print "refreshing stats for all files in all projects"
      self.potree.refreshstats()

  def generateactivationcode(self):
    """generates a unique activation code"""
    return "".join(["%02x" % int(random.random()*0x100) for i in range(16)])

  def getuserlanguage(self, request):
    """gets the language for a user who does not specify one in the URL"""
    raise NotImplementedError()
    #return session.language 

class PootleOptionParser(optparse.OptionParser):
  def __init__(self):
    versionstring = "%%prog %s\njToolkit %s\nTranslate Toolkit %s\nKid %s\nElementTree %s\nPython %s (on %s/%s)" % (pootleversion.ver, jtoolkitversion.ver, toolkitversion.sver, kid.__version__, ElementTree.VERSION, sys.version, sys.platform, os.name)
    optparse.OptionParser.__init__(self)
    self.set_default('prefsfile', filelocations.prefsfile)
    self.set_default('instance', 'Pootle')
    self.set_default('htmldir', filelocations.htmldir)
    self.add_option('', "--refreshstats", dest="action", action="store_const", const="refreshstats",
        default="runwebserver", help="refresh the stats files instead of running the webserver")
    self.add_option('', "--statsdb_file", action="store", type="string", dest="statsdb_file",
                    default=None, help="Specifies the location of the SQLite stats db file.")
    self.add_option('', "--no_cache_templates", action="store_false", dest="cache_templates", default=True,
                    help="Pootle should not cache templates, but reload them with every request.")
    self.add_option('', "--port", action="store", type="int", dest="port", default="8080",
                    help="The TCP port on which the server should listen for new connections.")

def checkversions():
  """Checks that version dependencies are met"""
  if not hasattr(toolkitversion, "build") or toolkitversion.build < 12000:
    raise RuntimeError("requires Translate Toolkit version >= 1.1.  Current installed version is: %s" % toolkitversion.sver)

def set_stats_db(options):
  prefs.config_db(pan_app.prefs)
  if options.statsdb_file is not None:
    statistics.STATS_OPTIONS['database'] = options.statsdb_file

def set_template_caching(options):
  if options.cache_templates is not None:
    pan_app.cache_templates = options.cache_templates

def set_options(options):
  pan_app.prefs = prefs.load_preferences(options.prefsfile)
  set_stats_db(options)
  set_template_caching(options)                                        
  server.options = options

def run_pootle(options, args):
  pan_app.pootle_server = PootleServer()
  if options.action == "runwebserver":
    httpd = make_server('', options.port, WSGIHandler())
    httpd.serve_forever()
  elif options.action == "refreshstats":
    pan_app.pootle_server.refreshstats(args)

def init_globals():
  import potree
  pan_app._po_tree = potree.POTree()

def get_lang(code):
  return pan_app.get_po_tree().getproject(code, 'pootle')

def check_for_language(code):
  return Project.objects.filter(code='pootle').count() > 0 and Language.objects.filter(code=code).count() > 0

def setup_localization_system():
  gettext.get_lang = get_lang
  gettext.check_for_language = check_for_language

def main():
  # run the web server
  init_globals()
  setup_localization_system()
  checkversions()
  parser = PootleOptionParser()
  options, args = parser.parse_args()
  if options.action != "runwebserver":
    options.servertype = "dummy"
  set_options(options)
  run_pootle(options, args)                                        

if __name__ == '__main__':
  main()


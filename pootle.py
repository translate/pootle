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
from Pootle import potree
from Pootle import pootlefile
from Pootle import users
from Pootle import filelocations
from translate.misc import optrecurse
# Versioning information
from Pootle import __version__ as pootleversion
from translate import __version__ as toolkitversion
from jToolkit import __version__ as jtoolkitversion
from Pootle import statistics
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

class PootleServer(users.OptionalLoginAppServer, templateserver.TemplateServer):
  """the Server that serves the Pootle Pages"""
  def __init__(self, instance, webserver, sessioncache=None, errorhandler=None, loginpageclass=users.LoginPage):
    if sessioncache is None:
      sessioncache = session.SessionCache(sessionclass=users.PootleSession)
    self.potree = potree.POTree(instance)
    super(PootleServer, self).__init__(instance, webserver, sessioncache, errorhandler, loginpageclass)
    self.templatedir = filelocations.templatedir
    self.setdefaultoptions()

  def loadurl(self, filename, context):
    """loads a url internally for overlay code"""
    # print "call to load %s with context:\n%s" % (filename, pprint.pformat(context))
    filename = os.path.join(self.templatedir, filename+os.extsep+"html")
    if os.path.exists(filename):
      return open(filename, "r").read()
    return None

  def saveprefs(self):
    """saves any changes made to the preferences"""
    # TODO: this is a hack, fix it up nicely :-)
    prefsfile = self.instance.__root__.__dict__["_setvalue"].im_self
    prefsfile.savefile()

  def setdefaultoptions(self):
    """sets the default options in the preferences"""
    changed = False
    if not hasattr(self.instance, "title"):
      setattr(self.instance, "title", "Pootle Demo")
      changed = True
    if not hasattr(self.instance, "description"):
      defaultdescription = "This is a demo installation of pootle. The administrator can customize the description in the preferences."
      setattr(self.instance, "description", defaultdescription)
      changed = True
    if not hasattr(self.instance, "baseurl"):
      setattr(self.instance, "baseurl", "/")
      changed = True
    if not hasattr(self.instance, "enablealtsrc"):
      setattr(self.instance, "enablealtsrc", False)
      changed = True
    if changed:
      self.saveprefs()

  def changeoptions(self, argdict):
    """changes options on the instance"""
    for key, value in argdict.iteritems():
      if not key.startswith("option-"):
        continue
      optionname = key.replace("option-", "", 1)
      setattr(self.instance, optionname, value)
    self.saveprefs()

  def initlanguage(self, req, session):
    """Initialises the session language from the request"""
    availablelanguages = self.potree.getlanguagecodes('pootle')
    acceptlanguageheader = req.headers_in.getheader('Accept-Language')
    if not acceptlanguageheader:
      return

    for langpref in acceptlanguageheader.split(","):
      langpref = pagelayout.localelanguage(langpref)
      pos = langpref.find(";")
      if pos >= 0:
        langpref = langpref[:pos]
      if langpref in availablelanguages:
        session.setlanguage(langpref)
        return
      elif langpref.startswith("en"):
        session.setlanguage(None)
        return
    session.setlanguage(None)

  def inittranslation(self, localedir=None, localedomains=None, defaultlanguage=None):
    """initializes live translations using the Pootle PO files"""
    self.localedomains = ['jToolkit', 'pootle']
    self.localedir = None
    self.languagelist = self.potree.getlanguagecodes('pootle')
    self.defaultlanguage = defaultlanguage
    if self.defaultlanguage is None:
      self.defaultlanguage = getattr(self.instance, "defaultlanguage", "en")
    if self.potree.hasproject(self.defaultlanguage, 'pootle'):
      try:
        self.translation = self.potree.getproject(self.defaultlanguage, 'pootle')
        return
      except Exception, e:
        self.errorhandler.logerror("Could not initialize translation:\n%s" % str(e))
    # if no translation available, set up a blank translation
    super(PootleServer, self).inittranslation()

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
          if projectcode and languagecode:
            dummyproject.savequickstats()
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

  def generaterobotsfile(self):
    """generates the robots.txt file"""
    langcodes = self.potree.getlanguagecodes()
    excludedfiles = ["login.html", "register.html", "activate.html"]
    content = "User-agent: *\n"
    for excludedfile in excludedfiles:
      content += "Disallow: /%s\n" % excludedfile
    for langcode in langcodes:
      content += "Disallow: /%s/\n" % langcode
    return content

  def getpage(self, pathwords, session, argdict):
    """return a page that will be sent to the user"""
    #Ensure we get unicode from argdict
    #TODO: remove when jToolkit does this
    newargdict = {}
    for key, value in argdict.iteritems():
      if isinstance(key, str):
       key = key.decode("utf-8")
      if isinstance(value, str):
       value = value.decode("utf-8")
      newargdict[key] = value
    argdict = newargdict

    # Strip of the base url
    baseurl = re.sub('http://[^/]', '', self.instance.baseurl)
    # Split up and remove empty parts
    basepathwords = filter(None, baseurl.split('/'))
    while pathwords and basepathwords and basepathwords[0] == pathwords[0]:
      basepathwords = basepathwords[1:]
      pathwords = pathwords[1:]

    if pathwords:
      top = pathwords[0]
    else:
      top = ""
    if top == 'js':
      pathwords = pathwords[1:]
      jsfile = os.path.join(filelocations.htmldir, 'js', *pathwords)
      if not os.path.exists(jsfile):
        jsfile = os.path.join(filelocations.jtoolkitdir, 'js', *pathwords)
        if not os.path.exists(jsfile):
          return None
      jspage = widgets.PlainContents(None)
      jspage.content_type = "application/x-javascript"
      jspage.sendfile_path = jsfile
      jspage.allowcaching = True
      return jspage
    elif pathwords and pathwords[-1].endswith(".css"):
      cssfile = os.path.join(filelocations.htmldir, *pathwords)
      if not os.path.exists(cssfile):
        cssfile = os.path.join(filelocations.jtoolkitdir, *pathwords)
        if not os.path.exists(cssfile):
          return None
      csspage = widgets.PlainContents(None)
      csspage.content_type = "text/css"
      csspage.sendfile_path = cssfile
      csspage.allowcaching = True
      return csspage
    elif top in ['selenium', 'tests']:
      picturefile = os.path.join(filelocations.htmldir, *pathwords)
      picture = widgets.SendFile(picturefile)
      if picturefile.endswith(".html"):
        picture.content_type = 'text/html'
      elif picturefile.endswith(".js"):
        picture.content_type = 'text/javascript'
      picture.allowcaching = True
      return picture
    elif top == 'images':
      pathwords = pathwords[1:]
      picturefile = os.path.join(filelocations.htmldir, 'images', *pathwords)
      picture = widgets.SendFile(picturefile)
      picture.content_type = thumbgallery.getcontenttype(pathwords[-1])
      picture.allowcaching = True
      return picture
    elif pathwords and pathwords[-1].endswith(".ico"):
      picturefile = os.path.join(filelocations.htmldir, *pathwords)
      picture = widgets.SendFile(picturefile)
      picture.content_type = 'image/ico'
      picture.allowcaching = True
      return picture
    elif top == "robots.txt":
      robotspage = widgets.PlainContents(self.generaterobotsfile())
      robotspage.content_type = 'text/plain'
      robotspage.allowcaching = True
      return robotspage
    elif top == "testtemplates.html":
      return templateserver.TemplateServer.getpage(self, pathwords, session, argdict)
    elif not top or top == "index.html":
      return indexpage.PootleIndex(self.potree, session)
    elif top == 'about.html':
      return indexpage.AboutPage(session)
    elif top == "login.html":
      if session.isopen:
        returnurl = argdict.get('returnurl', None) or getattr(self.instance, 'homepage', 'home/')
        return server.Redirect(returnurl)
      message = None
      if 'username' in argdict:
        session.username = argdict["username"]
        message = session.localize("Login failed")
      return users.LoginPage(session, languagenames=self.potree.getlanguages("pootle"), message=message)
    elif top == "register.html":
      return self.registerpage(session, argdict)
    elif top == "activate.html":
      return self.activatepage(session, argdict)
    elif top == "projects":
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
      else:
        top = ""
      if not top or top == "index.html":
        return indexpage.ProjectsIndex(self.potree, session)
      else:
        projectcode = top
        if not self.potree.hasproject(None, projectcode):
          return None
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
        else:
          top = ""
        if not top or top == "index.html":
          return indexpage.ProjectLanguageIndex(self.potree, projectcode, session)
        elif top == "admin.html":
          return adminpages.ProjectAdminPage(self.potree, projectcode, session, argdict)
    elif top == "languages":
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
      else:
        top = ""
      if not top or top == "index.html":
        return indexpage.LanguagesIndex(self.potree, session)
    elif top == "home":
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
      else:
        top = ""
      if not session.isopen:
        templatename = "redirect"
        templatevars = {
            "pagetitle": session.localize("Redirecting to login..."),
            "refresh": 1,
            "refreshurl": "login.html",
            "message": session.localize("Need to log in to access home page"),
            }
        pagelayout.completetemplatevars(templatevars, session)
        return server.Redirect("../login.html", withtemplate=(templatename, templatevars))
      if not top or top == "index.html":
        return indexpage.UserIndex(self.potree, session)
      elif top == "options.html":
        message = None
        try:
          if "changeoptions" in argdict:
            session.setoptions(argdict)
          if "changepersonal" in argdict:
            session.setpersonaloptions(argdict)
            message = session.localize("Personal details updated")
          if "changeinterface" in argdict:
            session.setinterfaceoptions(argdict)
        except users.RegistrationError, errormessage:
          message = errormessage
        return users.UserOptions(self.potree, session, message)
    elif top == "admin":
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
      else:
        top = ""
      if not session.isopen:
        templatename = "redirect"
        templatevars = {
            "pagetitle": session.localize("Redirecting to login..."),
            "refresh": 1,
            "refreshurl": "login.html",
            "message": session.localize("Need to log in to access admin page"),
            }
        pagelayout.completetemplatevars(templatevars, session)
        return server.Redirect("../login.html", withtemplate=(templatename, templatevars))
      if not session.issiteadmin():
        templatename = "redirect"
        templatevars = {
            "pagetitle": session.localize("Redirecting to home..."),
            "refresh": 1,
            "refreshurl": "login.html",
            "message": self.localize("You do not have the rights to administer pootle."),
            }
        pagelayout.completetemplatevars(templatevars, session)
        return server.Redirect("../index.html", withtemplate=(templatename, templatevars))
      if not top or top == "index.html":
        if "changegeneral" in argdict:
          self.changeoptions(argdict)
        return adminpages.AdminPage(self.potree, session, self.instance)
      elif top == "users.html":
        if "changeusers" in argdict:
          self.changeusers(session, argdict)
        return adminpages.UsersAdminPage(self, session.loginchecker.users, session, self.instance)
      elif top == "languages.html":
        if "changelanguages" in argdict:
          self.potree.changelanguages(argdict)
        return adminpages.LanguagesAdminPage(self.potree, session, self.instance)
      elif top == "projects.html":
        if "changeprojects" in argdict:
          self.potree.changeprojects(argdict)
        return adminpages.ProjectsAdminPage(self.potree, session, self.instance)
    elif top == "templates" or self.potree.haslanguage(top):
      languagecode = top
      pathwords = pathwords[1:]
      if pathwords:
        top = pathwords[0]
        bottom = pathwords[-1]
      else:
        top = ""
        bottom = ""
      if not top or top == "index.html":
        return indexpage.LanguageIndex(self.potree, languagecode, session)
      if self.potree.hasproject(languagecode, top):
        projectcode = top
        project = self.potree.getproject(languagecode, projectcode)
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
        else:
          top = ""
        if not top or top == "index.html":
          return indexpage.ProjectIndex(project, session, argdict)
        elif top == "admin.html":
          return adminpages.TranslationProjectAdminPage(self.potree, project, session, argdict)
        elif bottom == "translate.html":
          if len(pathwords) > 1:
            dirfilter = os.path.join(*pathwords[:-1])
          else:
            dirfilter = ""
          try:
            argdict["translate"] = 1
            return translatepage.TranslatePage(project, session, argdict, dirfilter)
          except projects.RightsError, stoppedby:
            argdict["message"] = str(stoppedby)
            return indexpage.ProjectIndex(project, session, argdict, dirfilter)
        elif bottom == "spellcheck.html":
          # the full review page
          argdict["spellchecklang"] = languagecode
          return spellui.SpellingReview(session, argdict, js_url="/js/spellui.js")
        elif bottom == "spellingstandby.html":
          # a simple 'loading' page
          return spellui.SpellingStandby()
        elif bottom.endswith("." + project.fileext):
          pofilename = os.path.join(*pathwords)
          if argdict.get("translate", 0):
            try:
              return translatepage.TranslatePage(project, session, argdict, dirfilter=pofilename)
            except projects.RightsError, stoppedby:
              if len(pathwords) > 1:
                dirfilter = os.path.join(*pathwords[:-1])
              else:
                dirfilter = ""
              argdict["message"] = str(stoppedby)
              return indexpage.ProjectIndex(project, session, argdict, dirfilter=dirfilter)
          elif argdict.get("index", 0):
            return indexpage.ProjectIndex(project, session, argdict, dirfilter=pofilename)
          else:
            pofile = project.getpofile(pofilename, freshen=False)
            page = widgets.SendFile(pofile.filename)
            page.etag = str(pofile.pomtime)
            encoding = getattr(pofile, "encoding", "UTF-8")
            page.content_type = "text/plain; charset=%s" % encoding
            return page
        elif bottom.endswith(".csv") or bottom.endswith(".xlf") or bottom.endswith(".ts") or bottom.endswith(".po") or bottom.endswith(".mo"):
          destfilename = os.path.join(*pathwords)
          basename, extension = os.path.splitext(destfilename)
          pofilename = basename + os.extsep + project.fileext
          extension = extension[1:]
          if extension == "mo":
            if not "pocompile" in project.getrights(session):
              return None
          etag, filepath_or_contents = project.convert(pofilename, extension)
          if etag:
            page = widgets.SendFile(filepath_or_contents)
            page.etag = str(etag)
          else:
            page = widgets.PlainContents(filepath_or_contents)
          if extension == "po":
            page.content_type = "text/x-gettext-translation; charset=UTF-8"
          elif extension == "csv":
            page.content_type = "text/csv; charset=UTF-8"
          elif extension == "xlf":
            page.content_type = "application/x-xliff; charset=UTF-8"
          elif extension == "ts":
            page.content_type = "application/x-linguist; charset=UTF-8"
          elif extension == "mo":
            page.content_type = "application/x-gettext-translation"
          return page
        elif bottom.endswith(".zip"):
          if not "archive" in project.getrights(session):
            return None
          if len(pathwords) > 1:
            dirfilter = os.path.join(*pathwords[:-1])
          else:
            dirfilter = None
          goal = argdict.get("goal", None)
          if goal:
            goalfiles = project.getgoalfiles(goal)
            pofilenames = []
            for goalfile in goalfiles:
              pofilenames.extend(project.browsefiles(goalfile))
          else:
            pofilenames = project.browsefiles(dirfilter)
          archivecontents = project.getarchive(pofilenames)
          page = widgets.PlainContents(archivecontents)
          page.content_type = "application/zip"
          return page
        elif bottom.endswith(".sdf") or bottom.endswith(".sgi"):
          if not "pocompile" in project.getrights(session):
            return None
          oocontents = project.getoo()
          page = widgets.PlainContents(oocontents)
          page.content_type = "text/tab-seperated-values"
          return page
        elif bottom == "index.html":
          if len(pathwords) > 1:
            dirfilter = os.path.join(*pathwords[:-1])
          else:
            dirfilter = None
          return indexpage.ProjectIndex(project, session, argdict, dirfilter)
        else:
          return indexpage.ProjectIndex(project, session, argdict, os.path.join(*pathwords))
    return None

  # I implemented buildpage and sendpage here so that jToolkit's template system could
  # be circumvented. This code originally comes from jToolkit and is still close to
  # the original code.

  def buildpage(self, filename, context, loadurl=None, localize=None, innerid=None):
    """build a response for the template with the vars in context"""
    context = templateserver.attribify(context)
    t = kid.Template(filename, **context)
    try:
      return t.serialize(output="xhtml")
    except Exception, e:
      tb = sys.exc_info()[2]
      tb_point = tb
      while tb_point.tb_next:
          tb_point = tb_point.tb_next
      ancestors = tb_point.tb_frame.f_locals.get("ancestors", [])
      xml_traceback = []
      for ancestor in ancestors:
          if ancestor is None: continue
          try:
            ancestor_str = str(ancestor)
            #ancestor_str = kid.et.tostring(ancestor)
          except Exception, e:
            ancestor_str = "(could not convert %s: %s)" % (str(ancestor), str(e))
          xml_traceback.append(ancestor_str)
      context_str = pprint.pformat(context)
      xml_traceback_str = "  " + "\n  ".join(xml_traceback)
      self.errorhandler.logerror("Error converting template: %s\nContext\n%s\nXML Ancestors:\n%s\n%s\n" % (e, context_str, xml_traceback_str, self.errorhandler.traceback_str()))
      if self.webserver.options.debug:
        import pdb
        pdb.post_mortem(tb)
      raise

  def sendpage(self, req, thepage):
    """bridge to widget code to allow templating to gradually replace it"""
    if kid is not None and hasattr(thepage, "templatename") and hasattr(thepage, "templatevars"):
      # renders using templates rather than the underlying widget class
      kid.enable_import(path=self.templatedir)
      #template = kid.Template(os.path.join(self.templatedir, thepage.templatename + ".html")) #self.gettemplate(thepage.templatename)
      loadurl = getattr(thepage, "loadurl", None)
      if loadurl is None:
        loadurl = getattr(self, "loadurl", None)
      pagestring = self.buildpage(os.path.join(self.templatedir, thepage.templatename + ".html"), thepage.templatevars, loadurl, req.session.localize)
      builtpage = widgets.PlainContents(pagestring)
      # make sure certain attributes are retained on the built page
      for copyattr in ('content_type', 'logresponse', 'sendfile_path', 'allowcaching', 'etag'):
        if hasattr(thepage, copyattr):
          setattr(builtpage, copyattr, getattr(thepage, copyattr))
      thepage = builtpage
    return super(PootleServer, self).sendpage(req, thepage)

class PootleOptionParser(simplewebserver.WebOptionParser):
  def __init__(self):
    versionstring = "%%prog %s\njToolkit %s\nTranslate Toolkit %s\nKid %s\nElementTree %s\nPython %s (on %s/%s)" % (pootleversion.ver, jtoolkitversion.ver, toolkitversion.ver, kid.__version__, ElementTree.VERSION, sys.version, sys.platform, os.name)
    simplewebserver.WebOptionParser.__init__(self, version=versionstring)
    self.set_default('prefsfile', filelocations.prefsfile)
    self.set_default('instance', 'Pootle')
    self.set_default('htmldir', filelocations.htmldir)
    self.add_option('', "--refreshstats", dest="action", action="store_const", const="refreshstats",
        default="runwebserver", help="refresh the stats files instead of running the webserver")
    psycomodes=["none", "full", "profile"]
    self.add_option('', "--statsdb_file", action="store", type="string", dest="statsdb_file",
                    default=None, help="Specifies the location of the SQLite stats db file.")
    self.add_option('', "--profile", action="store", type="string", dest="profile",
                    help="Perform profiling, storing the result to the supplied filename.")
    try:
      import psyco
      self.add_option('', "--psyco", dest="psyco", default=None, choices=psycomodes, metavar="MODE",
                      help="use psyco to speed up the operation, modes: %s" % (", ".join(psycomodes)))
    except ImportError, e:
      return

def checkversions():
  """Checks that version dependencies are met"""
  if not hasattr(toolkitversion, "build") or toolkitversion.build < 12000:
    raise RuntimeError("requires Translate Toolkit version >= 1.1.  Current installed version is: %s" % toolkitversion.ver)

def usepsyco(options):
  # options.psyco == None means the default, which is "full", but don't give a warning...
  # options.psyco == "none" means don't use psyco at all...
  if getattr(options, "psyco", "none") == "none":
    return
  try:
    import psyco
  except ImportError:
    if options.psyco is not None:
      optrecurse.RecursiveOptionParser(formats={}).warning("psyco unavailable", options, sys.exc_info())
    return
  if options.psyco is None:
    options.psyco = "full"
  if options.psyco == "full":
    psyco.full()
  elif options.psyco == "profile":
    psyco.profile()
  # tell psyco the functions it cannot compile, to prevent warnings
  import encodings
  psyco.cannotcompile(encodings.search_function)

def profile_runner(server, options):
  import cProfile
  import Pootle.profiling.lsprofcalltree as lsprofcalltree

  def write_cache_grind(profiler, file):
    k_cache_grind = lsprofcalltree.KCacheGrind(profiler)
    k_cache_grind.output(file)
    file.close()

  def do_profile_run(file):
    profiler = cProfile.Profile()
    try:
      profiler.runcall(simplewebserver.run, server, options)
    finally:
      write_cache_grind(profiler, file)

  try:
    profile_file = open(options.profile, "w+")
    do_profile_run(profile_file)
  except IOError, _e:
    print "Could not open profiling file %s" % (options.profile,)

def get_runner(options):
  if getattr(options, "profile", None) != None:
    return profile_runner
  else:
    return simplewebserver.run

def set_stats_db(server, options):
  def get_stats():
    if options.statsdb_file != None:
      return options.statsdb_file
    else:
      return getattr(server.instance, 'stats_db', None)

  statistics.STATS_DB_FILE = get_stats()

def main():
  # run the web server
  checkversions()
  parser = PootleOptionParser()
  options, args = parser.parse_args()
  options.errorlevel = options.logerrors
  usepsyco(options)
  if options.action != "runwebserver":
    options.servertype = "dummy"
  server = parser.getserver(options)
  set_stats_db(server, options)
  server.options = options
  if options.action == "runwebserver":
    run = get_runner(options)
    run(server, options)
  elif options.action == "refreshstats":
    server.refreshstats(args)

if __name__ == '__main__':
  main()


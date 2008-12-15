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
from Pootle.misc import prefs

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

  def changeoptions(self, argdict):
    """changes options on the instance"""
    prefs.change_preferences(pan_app.prefs, argdict)

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

  def getuserlanguage(self, request):
    """gets the language for a user who does not specify one in the URL"""
    raise NotImplementedError()
    #return session.language 

  @use_request_cache
  #@django_transaction
  def getpage(self, request, pathwords):
    """return a page that will be sent to the user"""

    def remove_from_list(lst):
      if len(lst) == 1:
        return lst[0]
      else:
        return lst

    def get_arg_dict(request):
      if request.method == 'GET':
        return request.GET
      else:
        return request.POST

    def process_django_request_args(request):
      return dict((key, remove_from_list(value)) for key, value in get_arg_dict(request).iteritems())

    arg_dict = process_django_request_args(request)

    pathwords = pathwords.split('/')
    # Strip of the base url
    baseurl = re.sub('https?://[^/]*', '', pan_app.prefs.baseurl)
    # Split up and remove empty parts
    basepathwords = filter(None, baseurl.split('/'))
    while pathwords and basepathwords and basepathwords[0] == pathwords[0]:
      basepathwords = basepathwords[1:]
      pathwords = pathwords[1:]
    
    if pathwords:
      top = pathwords[0]
    else:
      top = ""

    try:
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
        return templateserver.TemplateServer.getpage(self, pathwords, request, arg_dict)
      elif not top or top == "index.html":
        return indexpage.PootleIndex(request)
      elif top == 'about.html':
        return indexpage.AboutPage(request)
      elif top == "login.html":
        if 'doregister' in argdict:
          return self.registerpage(request, arg_dict)
# TODO: Figure out what to do here
#         try:
#           if session.usercreated:
#             session.usercreated = False
#             return server.Redirect('home/')
#         except:
#           pass
        if not request.user.is_anonymous(): # session.isopen:
          returnurl = argdict.get('returnurl', None) 
          if returnurl == None or re.search('[^A-Za-z0-9?./]+', returnurl):
            returnurl = getattr(pan_app.prefs, 'homepage', '/index.html')
          # TODO: This won't work. Do it the Django way.
          return server.Redirect(returnurl)
        message = None
        if 'username' in argdict:
          # TODO: Find another place to store the argdict["username"], so that we
          #       can correctly complain to the user if the login fails.
          #session.username = argdict["username"]
          message = request.localize("Login failed")
        return users.LoginPage(request, languagenames=self.languagenames, message=message)
      elif top == "register.html":
        return self.registerpage(request, argdict)
      elif top == "activate.html":
        return self.activatepage(request, argdict)
      elif top == "projects":
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
        else:
          top = ""
        if not top or top == "index.html":
          return indexpage.ProjectsIndex(request)
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
            return indexpage.ProjectLanguageIndex(projectcode, request)
          elif top == "admin.html":
            return adminpages.ProjectAdminPage(projectcode, request, argdict)
      elif top == "home":
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
        else:
          top = ""
        if request.user.is_anonymous(): #not session.isopen:
          templatename = "redirect"
          templatevars = {
              "pagetitle": request.localize("Redirecting to login..."),
              "refresh": 1,
              "refreshurl": "login.html",
              "message": request.localize("You need to log in to access your home page"),
              }
          pagelayout.completetemplatevars(templatevars, request)
          return server.Redirect("../login.html", withtemplate=(templatename, templatevars))
        if not top or top == "index.html":
          return indexpage.UserIndex(request)
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
          return users.UserOptions(session, message)
      elif top == "admin":
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
        else:
          top = ""
        if request.user.is_anonymous:
          templatename = "redirect"
          templatevars = {
              "pagetitle": session.localize("Redirecting to login..."),
              "refresh": 1,
              "refreshurl": "login.html",
              "message": session.localize("You must log in to administer Pootle."),
              }
          pagelayout.completetemplatevars(templatevars, request)
          return server.Redirect("../login.html", withtemplate=(templatename, templatevars))
        if not request.user.is_superuser:
          templatename = "redirect"
          templatevars = {
              "pagetitle": session.localize("Redirecting to home..."),
              "refresh": 1,
              "refreshurl": "login.html",
              "message": self.localize("You do not have the rights to administer pootle."),
              }
          pagelayout.completetemplatevars(templatevars, request)
          return server.Redirect("../index.html", withtemplate=(templatename, templatevars))
        if not top or top == "index.html":
          if "changegeneral" in argdict:
            self.changeoptions(argdict)
          return adminpages.AdminPage(request)
        elif top == "users.html":
          if "changeusers" in argdict:
            self.changeusers(session, argdict)
          return adminpages.UsersAdminPage(self, request)
        elif top == "languages.html":
          if "changelanguages" in argdict:
            self.potree.changelanguages(argdict)
          return adminpages.LanguagesAdminPage(request)
        elif top == "projects.html":
          if "changeprojects" in argdict:
            self.potree.changeprojects(argdict)
          return adminpages.ProjectsAdminPage(request)
      if not top or top == "index.html":
        return indexpage.LanguagesIndex(request)
      if top == "templates" or self.potree.haslanguage(top):
        languagecode = top
        pathwords = pathwords[1:]
        if pathwords:
          top = pathwords[0]
          bottom = pathwords[-1]
        else:
          top = ""
          bottom = ""
        if not top or top == "index.html":
          return indexpage.LanguageIndex(languagecode, request)
        if self.potree.hasproject(languagecode, top):
          projectcode = top
          project = self.potree.getproject(languagecode, projectcode)
          pathwords = pathwords[1:]
          if pathwords:
            top = pathwords[0]
          else:
            top = ""
          if not top or top == "index.html":
            try:
              return indexpage.ProjectIndex(project, request, arg_dict)
            except projects.RightsError, stoppedby:
              argdict["message"] = str(stoppedby)
              return indexpage.PootleIndex(request)
          elif top == "admin.html":
            return adminpages.TranslationProjectAdminPage(project, request, arg_dict)
          elif bottom == "translate.html":
            if len(pathwords) > 1:
              dirfilter = os.path.join(*pathwords[:-1])
            else:
              dirfilter = ""
            try:
              return translatepage.TranslatePage(project, request, arg_dict, dirfilter)
            except projects.RightsError, stoppedby:
              argdict["message"] = str(stoppedby)
              return indexpage.ProjectIndex(project, request, arg_dict, dirfilter)
          elif bottom == "spellcheck.html":
            # the full review page
            argdict["spellchecklang"] = languagecode
            return spellui.SpellingReview(session, argdict, js_url="/js/spellui.js")
          elif bottom == "spellingstandby.html":
            # a simple 'loading' page
            return spellui.SpellingStandby()
          elif bottom.endswith("." + project.fileext):
            pofilename = os.path.join(*pathwords)
            if arg_dict.get("translate", 0):
              try:
                return translatepage.TranslatePage(project, request, arg_dict, dirfilter=pofilename)
              except projects.RightsError, stoppedby:
                if len(pathwords) > 1:
                  dirfilter = os.path.join(*pathwords[:-1])
                else:
                  dirfilter = ""
                arg_dict["message"] = str(stoppedby)
                return indexpage.ProjectIndex(project, session, arg_dict, dirfilter=dirfilter)
            elif arg_dict.get("index", 0):
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
            return indexpage.ProjectIndex(project, request, argdict, dirfilter)
          else:
            return indexpage.ProjectIndex(project, request, argdict, os.path.join(*pathwords))
      return None
    except projects.Rights404Error:
      return None

  # I implemented buildpage and sendpage here so that jToolkit's template system could
  # be circumvented. This code originally comes from jToolkit and is still close to
  # the original code.

  def buildpage(self, filename, context, loadurl=None, localize=None, innerid=None):
    """build a response for the template with the vars in context"""
    context = templateserver.attribify(context)
    template_module = kid.load_template(filename, cache=pan_app.cache_templates)
    t = template_module.Template(filename, **context)
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
      kid.enable_import()
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

class PootleOptionParser(optparse.OptionParser):
  def __init__(self):
    versionstring = "%%prog %s\njToolkit %s\nTranslate Toolkit %s\nKid %s\nElementTree %s\nPython %s (on %s/%s)" % (pootleversion.ver, jtoolkitversion.ver, toolkitversion.ver, kid.__version__, ElementTree.VERSION, sys.version, sys.platform, os.name)
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
    raise RuntimeError("requires Translate Toolkit version >= 1.1.  Current installed version is: %s" % toolkitversion.ver)

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
  if options.action == "runwebserver":
    httpd = make_server('', options.port, WSGIHandler())
    httpd.serve_forever()
  elif options.action == "refreshstats":
    server.refreshstats(args)

def main():
  # run the web server
  checkversions()
  parser = PootleOptionParser()
  options, args = parser.parse_args()
  if options.action != "runwebserver":
    options.servertype = "dummy"
  set_options(options)
  run_pootle(options, args)                                        

if __name__ == '__main__':
  main()


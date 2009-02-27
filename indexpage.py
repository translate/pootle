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

from django.conf import settings
from django.utils.html import escape
from django.utils.translation import ugettext as _
N_ = _

from Pootle import pagelayout
from Pootle import projects
from Pootle import pootlefile
from translate.storage import versioncontrol
# Versioning information
from Pootle import __version__ as pootleversion
from translate import __version__ as toolkitversion
from Pootle.legacy.jToolkit import __version__ as jtoolkitversion
from kid import __version__ as kidversion
try:
  # ElementTree is part of Python 2.5, so let's try that first
  from xml.etree import ElementTree
except ImportError:
  from elementtree import ElementTree
import os
import sys
import re
import locale
import util  

from pootle_app.core import Suggestion, Submission, Language, Project
from pootle_app.profile import get_profile
from Pootle import pan_app
from Pootle.i18n.jtoolkit_i18n import localize, nlocalize, tr_lang
from pootle_app import project_tree

_undefined = lambda: None

def lazy(f):
  result = [_undefined]

  def evaluator():
    if result[0] != _undefined:
      return result[0]
    else:
      result[0] = f()
      return result[0]
  return evaluator

def shortdescription(descr):
  """Returns a short description by removing markup and only including up
  to the first br-tag"""
  stopsign = descr.find("<br")
  if stopsign >= 0:
    descr = descr[:stopsign]
  return re.sub("<[^>]*>", "", descr).strip()

def map_num_contribs(sub, user):
  user.num_contribs = sub.num_contribs
  return user

def users_form_suggestions(sugs):
  """Get the Users associated with the Suggestions. Also assign
  the num_contribs attribute from the Suggestion to the User"""
  return [map_num_contribs(sug, sug.suggester.user) for sug in sugs]

def users_form_submissions(subs):
  """Get the Users associated with the Submissions. Also assign
  the num_contribs attribute from the Submission to the User"""
  return [map_num_contribs(sub, sub.submitter.user) for sub in subs]

def gentopstats(topsugg, topreview, topsub, localize):
  ranklabel = localize("Rank")
  namelabel = localize("Name")
  topstats = []
  topstats.append({'data':        users_form_suggestions(topsugg), 
                   'headerlabel': localize('Suggestions'), 
                   'ranklabel':   ranklabel,
                   'namelabel':   namelabel, 
                   'vallabel':    localize('Suggestions')})
  topstats.append({'data':        users_form_suggestions(topreview),
                   'headerlabel': localize('Reviews'),
                   'ranklabel':   ranklabel,
                   'namelabel':   namelabel,
                   'vallabel':    localize('Reviews')})
  topstats.append({'data':        users_form_submissions(topsub),
                   'headerlabel': localize('Submissions'),
                   'ranklabel':   ranklabel,
                   'namelabel':   namelabel,
                   'vallabel':    localize('Submissions')})
  return topstats

def limit(query):
  return query[:5]

class AboutPage(pagelayout.PootlePage):
  """the bar at the side describing current login details etc"""
  def __init__(self, request):
    pagetitle = pan_app.get_title()
    description = pan_app.get_description()
    meta_description = shortdescription(description)
    keywords = ["Pootle", "locamotion", "translate", "translation", "localisation",
                "localization", "l10n", "traduction", "traduire"]
    abouttitle = localize("About Pootle")
    # l10n: Take care to use HTML tags correctly. A markup error could cause a display error.
    introtext = localize("<strong>Pootle</strong> is a simple web portal that should allow you to <strong>translate</strong>! Since Pootle is <strong>Free Software</strong>, you can download it and run your own copy if you like. You can also help participate in the development in many ways (you don't have to be able to program).")
    hosttext = localize('The Pootle project itself is hosted at <a href="http://translate.sourceforge.net/">translate.sourceforge.net</a> where you can find the details about source code, mailing lists etc.')
    # l10n: If your language uses right-to-left layout and you leave the English untranslated, consider enclosing the necessary text with <span dir="ltr">.......</span> to help browsers to display it correctly.
    # l10n: Take care to use HTML tags correctly. A markup error could cause a display error.
    nametext = localize('The name stands for <b>PO</b>-based <b>O</b>nline <b>T</b>ranslation / <b>L</b>ocalization <b>E</b>ngine, but you may need to read <a href="http://www.thechestnut.com/flumps.htm">this</a>.')
    versiontitle = localize("Versions")
    # l10n: If your language uses right-to-left layout and you leave the English untranslated, consider enclosing the necessary text with <span dir="ltr">.......</span> to help browsers to display it correctly.
    # l10n: Take care to use HTML tags correctly. A markup error could cause a display error.
    versiontext = localize("This site is running:<br />Pootle %s<br />Translate Toolkit %s<br />jToolkit %s<br />Kid %s<br />ElementTree %s<br />Python %s (on %s/%s)", pootleversion.ver, toolkitversion.sver, jtoolkitversion.ver, kidversion, ElementTree.VERSION, sys.version, sys.platform, os.name)
    templatename = "about"
    instancetitle = pan_app.get_title()
    templatevars = {"pagetitle": pagetitle, "description": description,
        "meta_description": meta_description, "keywords": keywords,
        "abouttitle": abouttitle, "introtext": introtext,
        "hosttext": hosttext, "nametext": nametext, "versiontitle": versiontitle, "versiontext": versiontext,
        "instancetitle": instancetitle}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

class PootleIndex(pagelayout.PootlePage):
  """The main page listing projects and languages. It is also reused for
  LanguagesIndex and ProjectsIndex"""
  def __init__(self, request):
    templatename = "index"
    description = pan_app.get_description()
    meta_description = shortdescription(description)
    keywords = ["Pootle", "WordForge", "translate", "translation", "localisation", "localization",
                "l10n", "traduction", "traduire"] + self.getprojectnames()
    languagelink = localize('Languages')
    projectlink = localize('Projects')
    instancetitle = pan_app.get_title()
    pagetitle = instancetitle
#@todo - need localized dates

    topsugg   = limit(Suggestion.objects.get_top_suggesters())
    topreview = limit(Suggestion.objects.get_top_reviewers())
    topsub    = limit(Submission.objects.get_top_submitters())
   
    topstats = gentopstats(topsugg, topreview, topsub, localize) 

    templatevars = {"pagetitle": pagetitle, "description": description,
        "meta_description": meta_description, "keywords": keywords,
        "languagelink": languagelink, "languages": self.getlanguages(request),
        "projectlink": projectlink, "projects": self.getprojects(request),
        # top users
        "topstats": topstats, "topstatsheading": localize("Top Contributors"),
        "instancetitle": instancetitle,
        "translationlegend": self.gettranslationsummarylegendl10n()
        }

    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

  def getlanguages(self, request):
    languages = []
    for language in Language.objects.get_latest_changes():
      projects_ = project_tree.get_projects(language)
      trans = 0
      fuzzy = 0
      total = 0
      viewable = False
      for project in projects_:
        translation_project = projects.get_translation_project(language, project)
        stats = translation_project.getquickstats()
        trans += stats['translatedsourcewords']
        fuzzy += stats['fuzzysourcewords']
        total += stats['totalsourcewords']
        rights = translation_project.getrights(request.user)
        viewable = viewable or ("view" in rights)
      untrans = total-trans-fuzzy
      try:
        transper = int(100*trans/total)
        fuzzyper = int(100*fuzzy/total)
        untransper = 100-transper-fuzzyper
      except ZeroDivisionError:
        transper = 100
        fuzzyper = 0 
        untransper = 0 

      lastact = ""
      if language.latest_change != None:
        lastact = language.latest_change

      if viewable:
        languages.append({"code": language.code, "name": tr_lang(language.fullname), "lastactivity": lastact, "trans": trans, "fuzzy": fuzzy, "untrans": untrans, "total": total, "transper": transper, "fuzzyper": fuzzyper, "untransper": untransper}) 
    languages.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    return languages

  def getprojects(self, request):
    """gets the options for the projects"""
    projects_ = []
    for project in Project.objects.get_latest_changes():
      languages = project_tree.get_languages(project)
      trans = 0
      fuzzy = 0
      total = 0
      viewable = False
      for language in languages:
        translation_project = projects.get_translation_project(language, project)
        stats = translation_project.getquickstats()
        trans += stats['translatedsourcewords']
        fuzzy += stats['fuzzysourcewords']
        total += stats['totalsourcewords']
        rights = translation_project.getrights(request.user)
        viewable = viewable or ("view" in rights)
      untrans = total-trans-fuzzy
      try:
        transper = int(100*trans/total)
        fuzzyper = int(100*fuzzy/total)
        untransper = 100-transper-fuzzyper
      except ZeroDivisionError:
        transper = 100
        fuzzyper = 0 
        untransper = 0 
      
      lastact = ""
      if project.latest_change != None:
        lastact = project.latest_change
      
      if viewable:
        projects_.append({"code": project.code, "name": project.fullname, "description": project.description, "lastactivity": lastact, "trans": trans, "fuzzy": fuzzy, "untrans": untrans, "total": total, "transper": transper, "fuzzyper": fuzzyper, "untransper": untransper})
    return projects_

  def getprojectnames(self):
    return [proj.fullname for proj in Project.objects.all()]

class UserIndex(pagelayout.PootlePage):
  """home page for a given user"""
  def __init__(self, request):
    self.request = request
    pagetitle = localize("User Page for: %s", request.user.username)
    templatename = "home"
    optionslink = localize("Change options")
    adminlink = localize("Admin page")
    admintext = localize("Administrate")
    quicklinkstitle = localize("Quick Links")
    instancetitle = pan_app.get_title()
    quicklinks = self.getquicklinks()
    setoptionstext = localize("You need to <a href='options.html'>choose your languages and projects</a>.")
    # l10n: %s is the full name of the currently logged in user
    statstitle = localize("%s's Statistics", request.user.first_name)
    statstext = {
                  'suggmade': localize("Suggestions Made"),
                  'suggaccepted': localize("Suggestions Accepted"),
                  'suggpending': localize("Suggestions Pending"),
                  'suggrejected': localize("Suggestions Rejected"),
                  'suggreviewed': localize("Suggestions Reviewed"),
                  'suggper': localize("Suggestion Use Percentage"),
                  'submade': localize("Submissions Made"),
                }
    templatevars = {"pagetitle": pagetitle, "optionslink": optionslink,
        "adminlink": adminlink, "admintext": admintext,
        "quicklinkstitle": quicklinkstitle,
        "quicklinks": quicklinks, "setoptionstext": setoptionstext,
        "instancetitle": instancetitle,
        "statstitle": statstitle, "statstext": statstext}
    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

  def getquicklinks(self):
    """gets a set of quick links to user's project-languages"""
    quicklinks = []
    user_profile = self.request.user.get_profile()
    # TODO: This can be done MUCH more efficiently with a bit of query
    # forethought. Why don't we just select all the TranslationProject
    # objects from the database which match the user's Languages and
    # Projects? This should be efficient.
    #
    # But this will only work once we move TranslationProject wholly
    # to the DB (and away from its current brain damaged
    # half-non-db/half-db implementation).
    for language in user_profile.languages.all():
      langlinks = []
      for project in user_profile.projects.all():
        try:
          projecttitle = project.fullname
          translation_project = projects.get_translation_project(language, project)
          isprojectadmin = "admin" in translation_project.getrights(self.request.user)
          langlinks.append({
            "code": project.code,
            "name": projecttitle,
            "isprojectadmin": isprojectadmin,
            "sep": "<br />"})
        except IndexError:
          pass
      if langlinks:
        langlinks[-1]["sep"] = ""
      quicklinks.append({"code": language.code, "name": tr_lang(language.fullname), "projects": langlinks})
      quicklinks.sort(cmp=locale.strcoll, key=lambda dict: dict["name"])
    return quicklinks

class ProjectsIndex(PootleIndex):
  """the list of languages"""
  def __init__(self, request):
    PootleIndex.__init__(self, request)
    self.templatename = "projects"

class LanguagesIndex(PootleIndex):
  """the list of languages"""
  def __init__(self, request):
    PootleIndex.__init__(self, request)
    self.templatename = "languages"

class LanguageIndex(pagelayout.PootleNavPage):
  """The main page for a language, listing all the projects in it"""
  def __init__(self, language, request):
    self.language = language
    self.languagecode = language.code
    self.languagename = language.fullname
    self.initpagestats()
    languageprojects = self.getprojects(request)
    if len(languageprojects) == 0:
      raise projects.Rights404Error
    self.projectcount = len(languageprojects)
    average = self.getpagestats()
    languagestats = nlocalize("%d project, average %d%% translated", "%d projects, average %d%% translated", self.projectcount, self.projectcount, average)
    languageinfo = self.getlanguageinfo()
    instancetitle = pan_app.get_title()
    # l10n: The first parameter is the name of the installation
    # l10n: The second parameter is the name of the project/language
    # l10n: This is used as a page title. Most languages won't need to change this
    pagetitle =  localize("%s: %s", instancetitle, tr_lang(self.languagename))
    templatename = "language"
    adminlink = localize("Admin")
    
    def narrow(query):
      return limit(query.filter(language__code=self.languagecode))

    topsugg     = narrow(Suggestion.objects.get_top_suggesters())
    topreview   = narrow(Suggestion.objects.get_top_reviewers())
    topsub      = narrow(Submission.objects.get_top_submitters())
   
    topstats = gentopstats(topsugg, topreview, topsub, localize) 

    templatevars = {"pagetitle": pagetitle,
        "language": {"code":  language.code, 
                     "name":  tr_lang(language.fullname),
                     "stats": languagestats,
                     "info":  languageinfo},
        "projects": languageprojects,
        "statsheadings": self.getstatsheadings(),
        "untranslatedtext": localize("%s untranslated words"),
        "fuzzytext": localize("%s fuzzy words"),
        "complete": localize("Complete"),
        # top users
        "topstats": topstats, "topstatsheading": localize("Top Contributors"),
        "instancetitle": instancetitle,
        "translationlegend": self.gettranslationsummarylegendl10n()
        }
    pagelayout.PootleNavPage.__init__(self, templatename, templatevars, request, bannerheight=80)

  def getlanguageinfo(self):
    """returns information defined for the language"""
    # specialchars = self.potree.getlanguagespecialchars(self.languagecode)
    nplurals = self.language.nplurals
    pluralequation = self.language.pluralequation
    infoparts = [(localize("Language Code"), self.languagecode),
                 (localize("Language Name"), tr_lang(self.languagename)),
                 # (localize("Special Characters"), specialchars),
                 (localize("Number of Plurals"), str(nplurals)),
                 (localize("Plural Equation"), pluralequation),
                ]
    return [{"title": title, "value": value} for title, value in infoparts]

  def getprojects(self, request):
    """gets the info on the projects"""
    projects_ = project_tree.get_projects(self.language)
    self.projectcount = len(projects_)
    translation_projects = [projects.get_translation_project(self.language, project) for project in projects_]
    projectitems = [self.getprojectitem(translation_project) for translation_project in translation_projects
                    if "view" in translation_project.getrights(request.user)]
    for n, item in enumerate(projectitems):
      item["parity"] = ["even", "odd"][n % 2]
    return projectitems

  def getprojectitem(self, translation_project):
    project = translation_project.project
    href = '%s/' % project.code
    projectdescription = shortdescription(project.description)
    projectstats = translation_project.getquickstats()
    projectdata = self.getstats(translation_project, projectstats)
    self.updatepagestats(projectdata["translatedsourcewords"], projectdata["totalsourcewords"])
    return {"code": project.code,
            "href": href,
            "icon": "folder",
            "title": project.fullname,
            "description": projectdescription,
            "data": projectdata,
            "isproject": True}

class ProjectLanguageIndex(pagelayout.PootleNavPage):
  """The main page for a project, listing all the languages belonging to it"""
  def __init__(self, project, request):
    self.project = project
    self.projectcode = project.code
    self.initpagestats()
    languages = self.getlanguages(request)
    if len(languages) == 0:
      raise projects.Rights404Error
    average = self.getpagestats()
    projectstats = nlocalize("%d language, average %d%% translated", "%d languages, average %d%% translated", self.languagecount, self.languagecount, average)
    projectname = self.project.fullname
    description = self.project.description
    meta_description = shortdescription(description)
    instancetitle = pan_app.get_title()
    # l10n: The first parameter is the name of the installation
    # l10n: The second parameter is the name of the project/language
    # l10n: This is used as a page title. Most languages won't need to change this
    pagetitle =  localize("%s: %s", instancetitle, projectname)
    templatename = "project"
    adminlink = localize("Admin")
    statsheadings = self.getstatsheadings()
    statsheadings["name"] = localize("Language")

    def narrow(query):
      return limit(query.filter(project=self.project))

    topsugg    = narrow(Suggestion.objects.get_top_suggesters())
    topreview  = narrow(Suggestion.objects.get_top_reviewers())
    topsub     = narrow(Submission.objects.get_top_submitters())

    topstats = gentopstats(topsugg, topreview, topsub, localize) 

    templatevars = {"pagetitle": pagetitle,
        "project": {"code": project.code, "name": project.fullname, "stats": projectstats},
        "description": description, "meta_description": meta_description,
        "adminlink": adminlink, "languages": languages,
        "untranslatedtext": localize("%s untranslated words"),
        "fuzzytext": localize("%s fuzzy words"),
        "complete": localize("Complete"),
        "instancetitle": instancetitle, 
        # top users
        "topstats": topstats, "topstatsheading": localize("Top Contributors"),
        "statsheadings": statsheadings,
        "translationlegend": self.gettranslationsummarylegendl10n()
        }
    pagelayout.PootleNavPage.__init__(self, templatename, templatevars, request, bannerheight=80)

  def getlanguages(self, request):
    """gets the stats etc of the languages"""
    languages = project_tree.get_languages(self.project)
    self.languagecount = len(languages)
    translation_projects = [projects.get_translation_project(language, self.project) for language in languages]
    languageitems = [self.getlanguageitem(translation_project) for translation_project in translation_projects
                     if "view" in translation_project.getrights(request.user)]
    languageitems.sort(cmp=locale.strcoll, key=lambda dict: dict["title"])
    for n, item in enumerate(languageitems):
      item["parity"] = ["even", "odd"][n % 2]
    return languageitems

  def getlanguageitem(self, translation_project):
    language = translation_project.language
    href = "../../%s/%s/" % (language.code, self.projectcode)
    quickstats = translation_project.getquickstats()
    data = self.getstats(translation_project, quickstats)
    self.updatepagestats(data["translatedsourcewords"], data["totalsourcewords"])
    return {"code": language.code, "icon": "language", "href": href, "title": tr_lang(language.fullname), "data": data}

class LazyStats(object):
  def __init__(self, project, pofilenames):
    self._project = project
    self._pofilenames = pofilenames
    self._basic = util.undefined
    self._assign = util.undefined
    self._units = util.undefined
  
  @util.lazy('_basic')
  def _get_basic(self):
    return self._project.getquickstats(self._pofilenames)
  basic = property(_get_basic)

  @util.lazy('_assign')
  def _get_assign(self):
    return self._project.combineassignstats(self._pofilenames)
  assign = property(_get_assign)

  @util.lazy('_units')
  def _get_units(self):
    return self._project.combine_unit_stats(self._pofilenames)
  units = property(_get_units)

class ProjectIndex(pagelayout.PootleNavPage):
  """The main page of a project in a specific language"""
  def __init__(self, translation_project, request, argdict, dirfilter=None):
    self.translation_project = translation_project
    language = translation_project.language
    project  = translation_project.project
    self.request = request
    self.rights = translation_project.getrights(request.user)
    if "view" not in self.rights:
      raise projects.Rights404Error()
    message = escape(request.GET.get("message", ""))
    if dirfilter == "":
      dirfilter = None
    self.dirfilter = dirfilter
    if dirfilter and dirfilter.endswith(".po"):
      self.dirname = os.path.dirname(dirfilter)
    else:
      self.dirname = dirfilter or ""
    self.argdict = argdict
    # handle actions before generating URLs, so we strip unneccessary parameters out of argdict
    self.handleactions()
    # generate the navigation bar maintaining state
    navbarpath_dict = self.makenavbarpath_dict(project=translation_project, request=self.request, currentfolder=dirfilter, argdict=self.argdict)
    self.showtracks = self.getboolarg("showtracks")
    self.showchecks = self.getboolarg("showchecks")
    self.showassigns = self.getboolarg("showassigns")
    self.showgoals = self.getboolarg("showgoals")
    self.editing = self.getboolarg("editing")
    self.currentgoal = self.argdict.pop("goal", None)
    if dirfilter and dirfilter.endswith(".po"):
      actionlinks = []
      mainstats = ""
      mainicon = "file"
    else:
      pofilenames = translation_project.browsefiles(dirfilter)
      projectstats = LazyStats(translation_project, pofilenames)
      if self.editing:
        actionlinks = self.getactionlinks("", projectstats, ["editing", "mine", "review", "check", "assign", "goal", "quick", "all", "zip", "sdf"], dirfilter)
      else:
        actionlinks = self.getactionlinks("", projectstats, ["editing", "goal", "zip", "sdf"])
      mainstats = self.getitemstats("", pofilenames, len(pofilenames))
    if self.showgoals:
      childitems = self.getgoalitems(dirfilter)
    else:
      childitems = self.getchilditems(dirfilter)
    instancetitle = pan_app.get_title()
    # l10n: The first parameter is the name of the installation (like "Pootle")
    pagetitle = localize("%s: Project %s, Language %s", instancetitle, project.fullname, tr_lang(language.fullname))
    templatename = "fileindex"

    reqstart = u""
    if dirfilter:
      reqstart = unicode(dirfilter)

    def narrow(query):
      return query.filter(project=project, language=language)[:5]

    topsugg    = narrow(Suggestion.objects.get_top_suggesters())
    topreview  = narrow(Suggestion.objects.get_top_reviewers())
    topsub     = narrow(Submission.objects.get_top_submitters())

    topstats = gentopstats(topsugg, topreview, topsub, localize) 

    templatevars = {"pagetitle": pagetitle,
        "project": {"code": project.code, "name": project.fullname},
        "language": {"code": language.code, "name": tr_lang(language.fullname)},
        # optional sections, will appear if these values are replaced
        "assign": None, "goals": None, "upload": None,
        "search": {"title": localize("Search"),
                   "advanced_title": localize("Advanced Search"),
                   "fields": self.getsearchfields() },
        "message": message,
        # navigation bar
        "navitems": [{"icon": "folder", "path": navbarpath_dict, "actions": actionlinks, "stats": mainstats}],
        # children
        "children": childitems,
        # are we in editing mode (otherwise stats)
        "editing": self.editing,
        # stats table headings
        "statsheadings": self.getstatsheadings(),
        # top users
        "topstats": topstats, "topstatsheading": localize("Top Contributors"),
        "untranslatedtext": localize("%s untranslated words"),
        "fuzzytext": localize("%s fuzzy words"),
        "complete": localize("Complete"),
        # general vars
        "instancetitle": instancetitle,
        "translationlegend": self.gettranslationsummarylegendl10n()
        }
    pagelayout.PootleNavPage.__init__(self, templatename, templatevars, request, bannerheight=80)
    if self.showassigns and "assign" in self.rights:
      self.templatevars["assign"] = self.getassignbox()
    if "admin" in self.rights:
      if self.showgoals:
        self.templatevars["goals"] = self.getgoalbox()
    if "admin" in self.rights or "translate" in self.rights or "suggest" in self.rights:
      self.templatevars["upload"] = self.getuploadbox()

  def handleactions(self):
    """handles the given actions that must be taken (changing operations)"""
    if "doassign" in self.argdict:
      assignto = self.argdict.pop("assignto", None)
      action = self.argdict.pop("action", None)
      if not assignto and action:
        raise ValueError("cannot doassign, need assignto and action")
      search = pootlefile.Search(dirfilter=self.dirfilter)
      assigncount = self.translation_project.assignpoitems(self.request, search, assignto, action)
      print "assigned %d strings to %s for %s" % (assigncount, assignto, action)
      del self.argdict["doassign"]
    if self.getboolarg("removeassigns"):
      assignedto = self.argdict.pop("assignedto", None)
      removefilter = self.argdict.pop("removefilter", "")
      if removefilter:
        if self.dirfilter:
          removefilter = self.dirfilter + removefilter
      else:
        removefilter = self.dirfilter
      search = pootlefile.Search(dirfilter=removefilter)
      search.assignedto = assignedto
      assigncount = self.translation_project.unassignpoitems(self.request, search, assignedto)
      print "removed %d assigns from %s" % (assigncount, assignedto)
      del self.argdict["removeassigns"]
    if "doupload" in self.argdict:
      extensiontypes = ("xlf", "xlff", "xliff", "po")
      if "Yes" in self.argdict.pop("dooverwrite", []):
        overwrite = True
      else:
        overwrite = False
      uploadfile = self.argdict.pop("uploadfile", None)
      # multiple translation file extensions check
      if filter(uploadfile.filename.endswith, extensiontypes):
        transfiles = True
      else:
        transfiles = False
      if not uploadfile.filename:
        raise ValueError(localize("Cannot upload file, no file attached"))
      if transfiles:
        self.translation_project.uploadfile(self.request, self.dirname, uploadfile.filename, uploadfile.contents, overwrite)
        self.translation_project.scanpofiles()
      elif uploadfile.filename.endswith(".zip"):
        self.translation_project.uploadarchive(self.request, self.dirname, uploadfile.contents)
        self.translation_project.scanpofiles()
      else:
        raise ValueError(localize("Can only upload PO files and zips of PO files"))
      del self.argdict["doupload"]
    if "doupdate" in self.argdict:
      updatefile = self.argdict.pop("updatefile", None)
      if not updatefile:
        raise ValueError("cannot update file, no file specified")
      if updatefile.endswith("." + self.translation_project.fileext):
        self.translation_project.updatepofile(self.request, self.dirname, updatefile)
        self.translation_project.scanpofiles()
      else:
        raise ValueError("can only update files with extension ." + self.translation_project.fileext)
      del self.argdict["doupdate"]
    if "docommit" in self.argdict:
      commitfile = self.argdict.pop("commitfile", None)
      if not commitfile:
        raise ValueError("cannot commit file, no file specified")
      if commitfile.endswith("." + self.translation_project.fileext):
        self.translation_project.commitpofile(self.request, self.dirname, commitfile)
      else:
        raise ValueError("can only commit files with extension ." + self.translation_project.fileext)
      del self.argdict["docommit"]
    if "doaddgoal" in self.argdict:
      goalname = self.argdict.pop("newgoal", None)
      if not goalname:
        raise ValueError("cannot add goal, no name given")
      self.translation_project.setgoalfiles(self.request, goalname.strip(), "")
      del self.argdict["doaddgoal"]
    if "doeditgoal" in self.argdict:
      goalnames = self.argdict.pop("editgoal", None)
      goalfile = self.argdict.pop("editgoalfile", None)
      if not goalfile:
        raise ValueError("cannot add goal, no filename given")
      if self.dirname:
        goalfile = os.path.join(self.dirname, goalfile)
      if not isinstance(goalnames, list):
        goalnames = [goalnames]
      goalnames = [goalname.strip() for goalname in goalnames if goalname.strip()]
      self.translation_project.setfilegoals(self.request, goalnames, goalfile)
      del self.argdict["doeditgoal"]
    if "doeditgoalusers" in self.argdict:
      goalname = self.argdict.pop("editgoalname", "").strip()
      if not goalname:
        raise ValueError("cannot edit goal, no name given")
      goalusers = self.translation_project.getgoalusers(goalname)
      addusername = self.argdict.pop("newgoaluser", "").strip()
      if addusername:
        self.translation_project.addusertogoal(self.request, goalname, addusername)
      del self.argdict["doeditgoalusers"]
    if "doedituser" in self.argdict:
      goalnames = self.argdict.pop("editgoal", None)
      goalusers = self.argdict.pop("editfileuser", "")
      goalfile = self.argdict.pop("editgoalfile", None)
      assignwhich = self.argdict.pop("edituserwhich", "all")
      if not goalfile:
        raise ValueError("cannot add user to file for goal, no filename given")
      if self.dirname:
        goalfile = os.path.join(self.dirname, goalfile)
      if not isinstance(goalusers, list):
        goalusers = [goalusers]
      goalusers = [goaluser.strip() for goaluser in goalusers if goaluser.strip()]
      if not isinstance(goalnames, list):
        goalnames = [goalnames]
      goalnames = [goalname.strip() for goalname in goalnames if goalname.strip()]
      search = pootlefile.Search(dirfilter=goalfile)
      if assignwhich == "all":
        pass
      elif assignwhich == "untranslated":
        search.matchnames = ["fuzzy", "untranslated"]
      elif assignwhich == "unassigned":
        search.assignedto = [None]
      elif assignwhich == "unassigneduntranslated":
        search.matchnames = ["fuzzy", "untranslated"]
        search.assignedto = [None]
      else:
        raise ValueError("unexpected assignwhich")
      for goalname in goalnames:
        action = "goal-" + goalname
        self.translation_project.reassignpoitems(self.request, search, goalusers, action)
      del self.argdict["doedituser"]
    # pop arguments we don't want to propogate through inadvertently...
    for argname in ("assignto", "action", "assignedto", "removefilter",
                    "uploadfile", "updatefile", "commitfile",
                    "newgoal", "editgoal", "editgoalfile", "editgoalname",
                    "newgoaluser", "editfileuser", "edituserwhich"):
      self.argdict.pop(argname, "")

  def getboolarg(self, argname, default=False):
    """gets a boolean argument from self.argdict"""
    value = self.argdict.get(argname, default)
    if isinstance(value, bool):
      return value
    elif isinstance(value, int):
      return bool(value)
    elif isinstance(value, (str, unicode)):
      value = value.lower()
      if value.isdigit():
        return bool(int(value))
      if value == "true":
        return True
      if value == "false":
        return False
    raise ValueError("Invalid boolean value for %s: %r" % (argname, value))

  def getassignbox(self):
    """adds a box that lets the user assign strings"""
    users = self.translation_project.getuserswithinterest()
    return {
      "users": users,
      "title": localize("Assign Strings"),
      "action_text": localize("Assign Action"),
      "users_text": localize("Assign to User"),
      "button": localize("Assign Strings")
    }

  def getgoalbox(self):
    """adds a box that lets the user add a new goal"""
    return {"title": localize('goals'),
            "name-title": localize("Enter goal name"),
            "button": localize("Add Goal")}

  def getuploadbox(self):
    """adds a box that lets the user assign strings"""
    uploadbox = {
            "title": localize("Upload File"),
            "file_title": localize("Select file to upload"),
            "upload_button": localize("Upload File")
            }
    if "admin" in self.rights or "overwrite" in self.rights:
      uploadbox.update({
            #l10n: radio button text
            "overwrite": localize("Overwrite"),
            #l10n: tooltip
            "overwrite_title": localize("Overwrite the current file if it exists"),
            #l10n: radio button text
            "merge": localize("Merge"),
            #l10n: tooltip
            "merge_title": localize("Merge the file with the current file and turn conflicts into suggestions"),
            })
    return uploadbox

  def getchilditems(self, dirfilter):
    """get all the items for directories and files viewable at this level"""
    if dirfilter is None:
      depth = 0
    else:
      depth = dirfilter.count(os.path.sep)
      if not dirfilter.endswith(os.path.extsep + self.translation_project.fileext):
        depth += 1
    diritems = []
    for childdir in self.translation_project.browsefiles(dirfilter=dirfilter, depth=depth, includedirs=True, includefiles=False):
      diritem = self.getdiritem(childdir)
      diritems.append((childdir, diritem))
    diritems.sort()
    fileitems = []
    for childfile in self.translation_project.browsefiles(dirfilter=dirfilter, depth=depth, includefiles=True, includedirs=False):
      fileitem = self.getfileitem(childfile)
      fileitems.append((childfile, fileitem))
    fileitems.sort()
    childitems = [diritem for childdir, diritem in diritems] + [fileitem for childfile, fileitem in fileitems]
    self.polarizeitems(childitems)
    return childitems

  def getitems(self, itempaths, linksrequired=None, **newargs):
    """gets the listed dir and fileitems"""
    diritems, fileitems = [], []
    for item in itempaths:
      if item.endswith(os.path.extsep + self.translation_project.fileext):
        fileitem = self.getfileitem(item, linksrequired=linksrequired, **newargs)
        fileitems.append((item, fileitem))
      else:
        if item.endswith(os.path.sep):
          item = item.rstrip(os.path.sep)
        diritem = self.getdiritem(item, linksrequired=linksrequired, **newargs)
        diritems.append((item, diritem))
      diritems.sort()
      fileitems.sort()
    childitems = [diritem for childdir, diritem in diritems] + [fileitem for childfile, fileitem in fileitems]
    self.polarizeitems(childitems)
    return childitems

  def getgoalitems(self, dirfilter):
    """get all the items for directories and files viewable at this level"""
    if dirfilter is None:
      depth = 0
    else:
      depth = dirfilter.count(os.path.sep)
      if not dirfilter.endswith(os.path.extsep + self.translation_project.fileext):
        depth += 1
    allitems = []
    goalchildren = {}
    allchildren = []
    for childname in self.translation_project.browsefiles(dirfilter=dirfilter, depth=depth, includedirs=True, includefiles=False):
      allchildren.append(childname + os.path.sep)
    for childname in self.translation_project.browsefiles(dirfilter=dirfilter, depth=depth, includedirs=False, includefiles=True):
      allchildren.append(childname)
    initial = dirfilter
    if initial and not initial.endswith(os.path.extsep + self.translation_project.fileext):
      initial += os.path.sep
    if initial:
      maxdepth = initial.count(os.path.sep)
    else:
      maxdepth = 0
    # using a goal of "" means that the file has no goal
    nogoal = ""
    if self.currentgoal is None:
      goalnames = self.translation_project.getgoalnames() + [nogoal]
    else:
      goalnames = [self.currentgoal]
    goalfiledict = {}
    for goalname in goalnames:
      goalfiles = self.translation_project.getgoalfiles(goalname, dirfilter, maxdepth=maxdepth, expanddirs=True, includepartial=True)
      goalfiles = [goalfile for goalfile in goalfiles if goalfile != initial]
      goalfiledict[goalname] = goalfiles
      for goalfile in goalfiles:
        goalchildren[goalfile] = True
    goalless = []
    for item in allchildren:
      itemgoals = self.translation_project.getfilegoals(item)
      if not itemgoals:
        goalless.append(item)
    goalfiledict[nogoal] = goalless
    for goalname in goalnames:
      goalfiles = goalfiledict[goalname]
      goalusers = self.translation_project.getgoalusers(goalname)
      goalitem = self.getgoalitem(goalname, dirfilter, goalusers)
      allitems.append(goalitem)
      if self.currentgoal == goalname:
        goalchilditems = self.getitems(goalfiles, linksrequired=["editgoal"], goal=self.currentgoal)
        allitems.extend(goalchilditems)
    return allitems

  def getgoalitem(self, goalname, dirfilter, goalusers):
    """returns an item showing a goal entry"""
    pofilenames = self.translation_project.getgoalfiles(goalname, dirfilter, expanddirs=True, includedirs=False)
    goal = {"actions": None, "icon": "goal", "isgoal": True, "goal": {"name": goalname}}
    if goalname:
      goal["title"] = goalname
    else:
      goal["title"] = localize("Not in a goal")
    goal["href"] = self.makelink("index.html", goal=goalname)
    if pofilenames:
      actionlinks = self.getactionlinks("", LazyStats(self.translation_project, pofilenames), linksrequired=["mine", "review", "translate", "zip"], goal=goalname)
      goal["actions"] = actionlinks
    goaluserslist = []
    if goalusers:
      goalusers.sort()
      goaluserslist = [{"name": goaluser, "sep": ", "} for goaluser in goalusers]
      if goaluserslist:
        goaluserslist[-1]["sep"] = ""
    goal["goal"]["users"] = goaluserslist
    if goalname and self.currentgoal == goalname:
      if "admin" in self.rights:
        unassignedusers = self.translation_project.getuserswithinterest()
        for user in goalusers:
          if user in unassignedusers:
            unassignedusers.pop(user)
        goal["goal"]["show_adduser"] = True
        goal["goal"]["otherusers"] = unassignedusers
        goal["goal"]["adduser_title"] = localize("Add User")
    goal["stats"] = self.getitemstats("", pofilenames, len(pofilenames), {'goal': goalname})
    projectstats = self.translation_project.getquickstats(pofilenames)
    goal["data"] = self.getstats(self.translation_project, projectstats)
    return goal

  def getdiritem(self, direntry, linksrequired=None, **newargs):
    """returns an item showing a directory entry"""
    pofilenames = self.translation_project.browsefiles(direntry)
    basename = os.path.basename(direntry)
    browseurl = self.getbrowseurl("%s/" % basename, **newargs)
    diritem = {"href": browseurl, "title": basename, "icon": "folder", "isdir": True}
    basename += "/"
    actionlinks = self.getactionlinks(basename, LazyStats(self.translation_project, pofilenames), linksrequired=linksrequired)
    diritem["actions"] = actionlinks
    if self.showgoals and "goal" in self.argdict:
      goalfilenames = self.translation_project.getgoalfiles(self.currentgoal, dirfilter=direntry, includedirs=False, expanddirs=True)
      diritem["stats"] = self.getitemstats(basename, goalfilenames, (len(goalfilenames), len(pofilenames)))
      projectstats = self.translation_project.getquickstats(goalfilenames)
      diritem["data"] = self.getstats(self.translation_project, projectstats)
    else:
      diritem["stats"] = self.getitemstats(basename, pofilenames, len(pofilenames))
      projectstats = self.translation_project.getquickstats(pofilenames)
      diritem["data"] = self.getstats(self.translation_project, projectstats)
    return diritem

  def getfileitem(self, fileentry, linksrequired=None, **newargs):
    """returns an item showing a file entry"""
    if linksrequired is None:
      if fileentry.endswith('.po'):
        linksrequired = ["mine", "review", "quick", "all", "po", "xliff", "ts", "csv", "mo", "update", "commit"]
      else:
        linksrequired = ["mine", "review", "quick", "all", "po", "xliff", "update", "commit"]
    basename = os.path.basename(fileentry)
    browseurl = self.getbrowseurl(basename, **newargs)
    fileitem = {"href": browseurl, "title": basename, "icon": "file", "isfile": True}
    actions = self.getactionlinks(basename, LazyStats(self.translation_project, [fileentry]), linksrequired=linksrequired)
    actionlinks = actions["extended"]
    if "po" in linksrequired:
      poname = basename.replace(".xlf", ".po")
      polink = {"href": poname, "text": localize('PO file')}
      actionlinks.append(polink)
    if "xliff" in linksrequired and "translate" in self.rights:
      xliffname = basename.replace(".po", ".xlf")
      xlifflink = {"href": xliffname, "text": localize('XLIFF file')}
      actionlinks.append(xlifflink)
    if "ts" in linksrequired and "translate" in self.rights:
      tsname = basename.replace(".po", ".ts")
      tslink = {"href": tsname, "text": localize('Qt .ts file')}
      actionlinks.append(tslink)
    if "csv" in linksrequired and "translate" in self.rights:
      csvname = basename.replace(".po", ".csv")
      csvlink = {"href": csvname, "text": localize('CSV file')}
      actionlinks.append(csvlink)
    if "mo" in linksrequired:
      if self.translation_project.db_translation_project.project.createmofiles and "pocompile" in self.rights:
        moname = basename.replace(".po", ".mo")
        molink = {"href": moname, "text": localize('MO file')}
        actionlinks.append(molink)
    if "update" in linksrequired and "admin" in self.rights:
      if versioncontrol.hasversioning(os.path.join(self.translation_project.podir,
              self.dirname, basename)):
        # l10n: Update from version control (like CVS or Subversion)
        updatelink = {"href": "index.html?editing=1&doupdate=1&updatefile=%s" % (basename), "text": localize('Update')}
        actionlinks.append(updatelink)
    if "commit" in linksrequired and "commit" in self.rights:
      if versioncontrol.hasversioning(os.path.join(self.translation_project.podir,
              self.dirname, basename)):
        # l10n: Commit to version control (like CVS or Subversion)
        commitlink = {"href": "index.html?editing=1&docommit=1&commitfile=%s" % (basename), "text": localize('Commit')}
        actionlinks.append(commitlink)
    # update the separators
    for n, actionlink in enumerate(actionlinks):
      if n < len(actionlinks)-1:
        actionlink["sep"] = " | "
      else:
        actionlink["sep"] = ""
    fileitem["actions"] = actions
    fileitem["stats"] = self.getitemstats(basename, [fileentry], None)
    fileitem["data"] = self.getstats(self.translation_project, self.translation_project.getquickstats([fileentry]))
    return fileitem

  def getgoalform(self, basename, goalfile, filegoals):
    """Returns a form for adjusting goals"""
    goalformname = "goal_%s" % (basename.replace("/", "_").replace(".", "_"))
    goalnames = self.translation_project.getgoalnames()
    useroptions = []
    for goalname in filegoals:
      useroptions += self.translation_project.getgoalusers(goalname)
    multifiles = None
    if len(filegoals) > 1:
      multifiles = "multiple"
    multiusers = None
    assignusers = []
    assignwhich = []
    if len(useroptions) > 1:
      assignfilenames = self.translation_project.browsefiles(dirfilter=goalfile)
      if self.currentgoal:
        action = "goal-" + self.currentgoal
      else:
        action = None
      assignstats = self.translation_project.combineassignstats(assignfilenames, action)
      assignusers = list(assignstats.iterkeys())
      useroptions += [username for username in assignusers if username not in useroptions]
      if len(assignusers) > 1:
        multiusers = "multiple"
      assignwhich = [('all', localize("All Strings")),
                     ('untranslated', localize("Untranslated")),
                     ('unassigned', localize('Unassigned')),
                     ('unassigneduntranslated', localize("Unassigned and Untranslated"))]
    return {
     "name": goalformname,
     "filename": basename,
     "goalnames": goalnames,
     "filegoals": dict([(goalname, goalname in filegoals or None) for goalname in goalnames]),
     "multifiles": multifiles,
     "setgoal_text": localize("Set Goal"),
     "users": useroptions,
     "assignusers": dict([(username, username in assignusers or None) for username in useroptions]),
     "multiusers": multiusers,
     "selectmultiple_text": localize("Select Multiple"),
     "assignwhich": [{"value": value, "text": text} for value, text in assignwhich],
     "assignto_text": localize("Assign To"),
     }

  def getactionlinks(self, basename, projectstats, linksrequired=None, filepath=None, goal=None):
    """get links to the actions that can be taken on an item (directory / file)"""
    if linksrequired is None:
      linksrequired = ["mine", "review", "quick", "all"]
    actionlinks = []
    actions = {}
    actions["goalform"] = None
    if not basename or basename.endswith("/"):
      baseactionlink = basename + "translate.html?"
      baseindexlink = basename + "index.html?"
    else:
      baseactionlink = "%s?translate=1" % basename
      baseindexlink = "%s?index=1" % basename
    if goal:
      baseactionlink += "&goal=%s" % goal
      baseindexlink += "&goal=%s" % goal
    def addoptionlink(linkname, rightrequired, attrname, showtext, hidetext):
      if linkname in linksrequired:
        if rightrequired and not rightrequired in self.rights:
          return
        if getattr(self, attrname, False):
          link = {"href": self.makelink(baseindexlink, **{attrname:0}), "text": hidetext}
        else:
          link = {"href": self.makelink(baseindexlink, **{attrname:1}), "text": showtext}
        link["sep"] = " | "
        actionlinks.append(link)
    addoptionlink("editing", None, "editing", localize("Show Editing Functions"),
                                              localize("Show Statistics"))
    addoptionlink("track", None, "showtracks", localize("Show Tracks"), localize("Hide Tracks"))
    # l10n: "Checks" are quality checks that Pootle performs on translations to test for common mistakes
    addoptionlink("check", "translate", "showchecks", localize("Show Checks"), localize("Hide Checks"))
    addoptionlink("goal", None, "showgoals", localize("Show Goals"), localize("Hide Goals"))
    addoptionlink("assign", "translate", "showassigns", localize("Show Assigns"), localize("Hide Assigns"))
    actions["basic"] = actionlinks
    actionlinks = []
    if not goal:
      goalfile = os.path.join(self.dirname, basename)
      filegoals = self.translation_project.getfilegoals(goalfile)
      if self.showgoals:
        if len(filegoals) > 1:
          #TODO: This is not making sense. For now make it an unclickable link
          allgoalslink = {"href": "", "text": localize("All Goals: %s", (", ".join(filegoals)))}
          actionlinks.append(allgoalslink)
      if "editgoal" in linksrequired and "admin" in self.rights:
        actions["goalform"] = self.getgoalform(basename, goalfile, filegoals)
    if "mine" in linksrequired and not self.request.user.is_anonymous:
      if "translate" in self.rights:
        minelink = localize("Translate My Strings")
      else:
        minelink = localize("View My Strings")
      mystats = projectstats.assign.get(self.request.user.username, [])
      if len(mystats):
        minelink = {"href": self.makelink(baseactionlink, assignedto=self.request.user.username), "text": minelink}
      else:
        minelink = {"title": localize("No strings assigned to you"), "text": minelink}
      actionlinks.append(minelink)
      if "quick" in linksrequired and "translate" in self.rights:
        if len(mystats) > 0: # A little shortcut to avoid the call to projectstats.units if we don't have anything assigned
          mytranslatedstats = [statsitem for statsitem in mystats if statsitem in projectstats.units.get("translated", [])]
        else:
          mytranslatedstats = []
        quickminelink = localize("Quick Translate My Strings")
        if len(mytranslatedstats) < len(mystats):
          quickminelink = {"href": self.makelink(baseactionlink, assignedto=self.request.user.username, fuzzy=1, untranslated=1), "text": quickminelink}
        else:
          quickminelink = {"title": localize("No untranslated strings assigned to you"), "text": quickminelink}
        actionlinks.append(quickminelink)
    if "review" in linksrequired and projectstats.units.get("check-hassuggestion", []):
      if "review" in self.rights:
        reviewlink = localize("Review Suggestions")
      else:
        reviewlink = localize("View Suggestions")
      reviewlink = {"href": self.makelink(baseactionlink, review=1, **{"hassuggestion": 1}), "text": reviewlink}
      actionlinks.append(reviewlink)
    if "quick" in linksrequired:
      if "translate" in self.rights:
        quicklink = localize("Quick Translate")
      else:
        quicklink = localize("View Untranslated")
      if projectstats.basic.get("translated", 0) < projectstats.basic.get("total", 0):
        quicklink = {"href": self.makelink(baseactionlink, fuzzy=1, untranslated=1), "text": quicklink}
      else:
        quicklink = {"title": localize("No untranslated items"), "text": quicklink}
      actionlinks.append(quicklink)
    if "all" in linksrequired and "translate" in self.rights:
      translatelink = {"href": self.makelink(baseactionlink), "text": localize('Translate All')}
      actionlinks.append(translatelink)
    if "zip" in linksrequired and "archive" in self.rights:
      if filepath and filepath.endswith(".po"):
        currentfolder = os.path.dirname(filepath)
      else:
        currentfolder = filepath
      archivename = "%s-%s" % (self.translation_project.projectcode, self.translation_project.languagecode)
      if currentfolder:
        archivename += "-%s" % currentfolder.replace(os.path.sep, "-")
      if goal:
        archivename += "-%s" % goal
      archivename += ".zip"
      if goal:
        archivename += "?goal=%s" % goal
        linktext = localize('ZIP of goal')
      else:
        linktext = localize('ZIP of folder')
      ziplink = {"href": archivename, "text": linktext, "title": archivename}
      actionlinks.append(ziplink)

    if "sdf" in linksrequired and "pocompile" in self.rights and \
        self.translation_project.ootemplate() and not (basename or filepath):
      archivename = self.translation_project.languagecode + ".sdf"
      linktext = localize('Generate SDF')
      oolink = {"href": archivename, "text": linktext, "title": archivename}
      actionlinks.append(oolink)
    for n, actionlink in enumerate(actionlinks):
      if n < len(actionlinks)-1:
        actionlink["sep"] = " | "
      else:
        actionlink["sep"] = ""
    actions["extended"] = actionlinks
    if not actions["extended"] and not actions["goalform"] and actions["basic"]:
      actions["basic"][-1]["sep"] = ""
    return actions

  def getitemstats(self, basename, pofilenames, numfiles, url_opts={}):
    """returns a widget summarizing item statistics"""
    stats = {"summary": self.describestats(self.translation_project, self.translation_project.getquickstats(pofilenames), numfiles), "checks": [], "tracks": [], "assigns": []}
    if not basename or basename.endswith("/"):
      linkbase = basename + "translate.html?"
    else:
      linkbase = basename + "?translate=1"
    if pofilenames:
      if self.showchecks:
        stats["checks"] = self.getcheckdetails(pofilenames, linkbase, url_opts)
      if self.showtracks:
        trackfilter = (self.dirfilter or "") + basename
        trackpofilenames = self.translation_project.browsefiles(trackfilter)
        projecttracks = self.translation_project.gettracks(trackpofilenames)
        stats["tracks"] = self.gettrackdetails(projecttracks, linkbase)
      if self.showassigns:
        if not basename or basename.endswith("/"):
          removelinkbase = "?showassigns=1&removeassigns=1"
        else:
          removelinkbase = "?showassigns=1&removeassigns=1&removefilter=%s" % basename
        stats["assigns"] = self.getassigndetails(pofilenames, linkbase, removelinkbase)
    return stats

  def gettrackdetails(self, projecttracks, linkbase):
    """return a list of strings describing the results of tracks"""
    return [trackmessage for trackmessage in projecttracks]

  def getcheckdetails(self, pofilenames, linkbase, url_opts={}):
    """return a list of strings describing the results of checks"""
    projectstats = self.translation_project.combine_unit_stats(pofilenames)
    total = max(len(projectstats.get("total", [])), 1)
    checklinks = []
    keys = projectstats.keys()
    keys.sort()
    for checkname in keys:
      if not checkname.startswith("check-"):
        continue
      checkcount = len(projectstats[checkname])
      checkname = checkname.replace("check-", "", 1)
      if total and checkcount:
        stats = nlocalize("%d string (%d%%) failed", "%d strings (%d%%) failed", checkcount, checkcount, (checkcount * 100 / total))
        url_opts[str(checkname)] = 1
        checklink = {"href": self.makelink(linkbase, **url_opts), "text": checkname, "stats": stats}
        del url_opts[str(checkname)]
        checklinks += [checklink]
    return checklinks

  def getassigndetails(self, pofilenames, linkbase, removelinkbase):
    """return a list of strings describing the assigned strings"""
    # TODO: allow setting of action, so goals can only show the appropriate action assigns
    # quick lookup of what has been translated
    projectstats = LazyStats(self.translation_project, pofilenames)
    totalcount = projectstats.basic.get("total", 0)
    totalwords = projectstats.basic.get("totalsourcewords", 0)
    assignlinks = []
    keys = projectstats.assign.keys()
    keys.sort()
    for assignname in keys:
      assigned = projectstats.assign[assignname]
      assigncount = len(assigned)
      assignwords = self.translation_project.countwords(assigned)
      complete = [statsitem for statsitem in assigned if statsitem in projectstats.units.get('translated', [])]
      completecount = len(complete)
      completewords = self.translation_project.countwords(complete)
      if totalcount and assigncount:
        assignlink = {"href": self.makelink(linkbase, assignedto=assignname), "text": assignname}
        percentassigned = assignwords * 100 / max(totalwords, 1)
        percentcomplete = completewords * 100 / max(assignwords, 1)
        stats = localize("%d/%d words (%d%%) assigned", assignwords, totalwords, percentassigned)
        stringstats = localize("[%d/%d strings]", assigncount, totalcount)
        completestats = localize("%d/%d words (%d%%) translated", completewords, assignwords, percentcomplete)
        completestringstats = localize("[%d/%d strings]", completecount, assigncount)
        if "assign" in self.rights:
          removetext = localize("Remove")
          removelink = {"href": self.makelink(removelinkbase, assignedto=assignname), "text": removetext}
        else:
          removelink = None
        assignlinks.append({"assign": assignlink, "stats": stats, "stringstats": stringstats, "completestats": completestats, "completestringstats": completestringstats, "remove": removelink})
    return assignlinks


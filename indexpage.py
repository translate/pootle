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

from django.utils.html import escape
from django.conf import settings
from django.utils.translation import ugettext as _
N_ = _

from translate.storage import versioncontrol
from translate import __version__ as toolkitversion

from pootle_app.core                import Suggestion, Submission, Language, Project
from pootle_app.fs_models           import Directory
from pootle_app.goals               import Goal
from pootle_app.profile             import get_profile
from pootle_app.translation_project import TranslationProject
from pootle_app.permissions         import get_matching_permissions
from pootle_app.language            import try_language_code
from pootle_app                     import project_tree

from Pootle.i18n.jtoolkit_i18n import nlocalize, tr_lang
from Pootle.legacy.jToolkit import __version__ as jtoolkitversion
from Pootle import pan_app, pagelayout, pootlefile
from Pootle import __version__ as pootleversion

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

def gentopstats(topsugg, topreview, topsub):
  ranklabel = _("Rank")
  namelabel = _("Name")
  topstats = []
  topstats.append({'data':        users_form_suggestions(topsugg), 
                   'headerlabel': _('Suggestions'),
                   'ranklabel':   ranklabel,
                   'namelabel':   namelabel, 
                   'vallabel':    _('Suggestions')})
  topstats.append({'data':        users_form_suggestions(topreview),
                   'headerlabel': _('Reviews'),
                   'ranklabel':   ranklabel,
                   'namelabel':   namelabel,
                   'vallabel':    _('Reviews')})
  topstats.append({'data':        users_form_submissions(topsub),
                   'headerlabel': _('Submissions'),
                   'ranklabel':   ranklabel,
                   'namelabel':   namelabel,
                   'vallabel':    _('Submissions')})
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
    abouttitle = _("About Pootle")
    # l10n: Take care to use HTML tags correctly. A markup error could cause a display error.
    introtext = _("<strong>Pootle</strong> is a simple web portal that should allow you to <strong>translate</strong>! Since Pootle is <strong>Free Software</strong>, you can download it and run your own copy if you like. You can also help participate in the development in many ways (you don't have to be able to program).")
    hosttext = _('The Pootle project itself is hosted at <a href="http://translate.sourceforge.net/">translate.sourceforge.net</a> where you can find the details about source code, mailing lists etc.')
    # l10n: If your language uses right-to-left layout and you leave the English untranslated, consider enclosing the necessary text with <span dir="ltr">.......</span> to help browsers to display it correctly.
    # l10n: Take care to use HTML tags correctly. A markup error could cause a display error.
    nametext = _('The name stands for <b>PO</b>-based <b>O</b>nline <b>T</b>ranslation / <b>L</b>ocalization <b>E</b>ngine, but you may need to read <a href="http://www.thechestnut.com/flumps.htm">this</a>.')
    versiontitle = _("Versions")
    # l10n: If your language uses right-to-left layout and you leave the English untranslated, consider enclosing the necessary text with <span dir="ltr">.......</span> to help browsers to display it correctly.
    # l10n: Take care to use HTML tags correctly. A markup error could cause a display error.
    versiontext = _("This site is running:<br />Pootle %s<br />Translate Toolkit %s<br />jToolkit %s<br />Kid %s<br />ElementTree %s<br />Python %s (on %s/%s)" % (pootleversion.ver, toolkitversion.sver, jtoolkitversion.ver, kidversion, ElementTree.VERSION, sys.version, sys.platform, os.name))
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
    languagelink = _('Languages')
    projectlink = _('Projects')
    instancetitle = pan_app.get_title()
    pagetitle = instancetitle

    topsugg   = limit(Suggestion.objects.get_top_suggesters())
    topreview = limit(Suggestion.objects.get_top_reviewers())
    topsub    = limit(Submission.objects.get_top_submitters())
   
    topstats = gentopstats(topsugg, topreview, topsub)
    language_index, project_index = TranslationProject.get_language_and_project_indices()
    permission_set = get_matching_permissions(get_profile(request.user), Directory.objects.root)
    templatevars = {
      "pagetitle":         pagetitle,
      "description":       description,
      "meta_description":  meta_description,
      "keywords":          keywords,
      "languagelink":      languagelink, 
      "languages":         self.getlanguages(request, language_index, permission_set),
      "projectlink":       projectlink,
      "projects":          self.getprojects(request, project_index, permission_set),
      # top users
      "topstats":          topstats,
      "topstatsheading":   _("Top Contributors"),
      "instancetitle":     instancetitle,
      "translationlegend": self.gettranslationsummarylegendl10n()
      }

    pagelayout.PootlePage.__init__(self, templatename, templatevars, request)

  def get_items(self, request, model, item_index, name_func, permission_set):
    def get_percentages(trans, fuzzy):
      try:
        transper = int(100.0 * trans / total)
        fuzzyper = int(100.0 * fuzzy / total)
        untransper = 100 - transper - fuzzyper
      except ZeroDivisionError:
        transper = 100
        fuzzyper = 0 
        untransper = 0 
      return transper, fuzzyper, untransper

    def get_last_action(item, latest_changes):
      if item.code in latest_changes and latest_changes[item.code] is not None:
        return latest_changes[item.code]
      else:
        return ""

    items = []
    if 'view' not in permission_set:
      return items
    latest_changes = model.objects.get_latest_changes()
    for item in [item for item in model.objects.all() if item.code in item_index]:
      trans = 0
      fuzzy = 0
      total = 0
      for translation_project in item_index[item.code]:
        stats = translation_project.directory.get_quick_stats(translation_project.checker)
        trans += stats['translatedsourcewords']
        fuzzy += stats['fuzzysourcewords']
        total += stats['totalsourcewords']
      untrans = total - trans - fuzzy
      transper, fuzzyper, untransper = get_percentages(trans, fuzzy)
      lastact = get_last_action(item, latest_changes)
      items.append({"code":         item.code,
                    "name":         name_func(item.fullname),
                    "lastactivity": lastact,
                    "trans":        trans,
                    "fuzzy":        fuzzy,
                    "untrans":      untrans,
                    "total":        total,
                    "transper":     transper,
                    "fuzzyper":     fuzzyper,
                    "untransper":   untransper}) 
    items.sort(lambda x,y: locale.strcoll(x["name"], y["name"]))
    return items

  def getlanguages(self, request, language_index, permission_set):
    return self.get_items(request, Language, language_index, tr_lang, permission_set)

  def getprojects(self, request, project_index, permission_set):
    return self.get_items(request, Project, project_index, lambda x: x, permission_set)

  def getprojectnames(self):
    return [proj.fullname for proj in Project.objects.all()]

class UserIndex(pagelayout.PootlePage):
  """home page for a given user"""
  def __init__(self, request):
    self.request = request
    pagetitle = _("User Page for: %s" % request.user.username)
    templatename = "home"
    optionslink = _("Change options")
    adminlink = _("Admin page")
    admintext = _("Administrate")
    quicklinkstitle = _("Quick Links")
    instancetitle = pan_app.get_title()
    quicklinks = self.getquicklinks()
    setoptionstext = _("You need to <a href='options.html'>choose your languages and projects</a>.")
    # l10n: %s is the full name of the currently logged in user
    statstitle = _("%s's Statistics" % request.user.first_name)
    statstext = {
                  'suggmade': _("Suggestions Made"),
                  'suggaccepted': _("Suggestions Accepted"),
                  'suggpending': _("Suggestions Pending"),
                  'suggrejected': _("Suggestions Rejected"),
                  'suggreviewed': _("Suggestions Reviewed"),
                  'suggper': _("Suggestion Use Percentage"),
                  'submade': _("Submissions Made"),
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
          translation_project = TranslationProject.objects.get(language=language, project=project)
          isprojectadmin = "admin" in get_matching_permissions(user_profile, translation_project.directory)
          langlinks.append({
            "code": project.code,
            "name": projecttitle,
            "isprojectadmin": isprojectadmin,
            "sep": "<br />"})
        except TranslationProject.DoesNotExist:
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
    pagetitle =  _("%s: %s" % (instancetitle, tr_lang(self.languagename)))
    templatename = "language"
    adminlink = _("Admin")
    
    def narrow(query):
      return limit(query.filter(translation_project__language__code=self.languagecode))

    topsugg     = narrow(Suggestion.objects.get_top_suggesters())
    topreview   = narrow(Suggestion.objects.get_top_reviewers())
    topsub      = narrow(Submission.objects.get_top_submitters())
   
    topstats = gentopstats(topsugg, topreview, topsub)

    templatevars = {"pagetitle": pagetitle,
        "language": {"code":  language.code, 
                     "name":  tr_lang(language.fullname),
                     "stats": languagestats,
                     "info":  languageinfo},
        "projects": languageprojects,
        "statsheadings": self.getstatsheadings(),
        "untranslatedtext": _("%s untranslated words"),
        "fuzzytext": _("%s fuzzy words"),
        "complete": _("Complete"),
        # top users
        "topstats": topstats, "topstatsheading": _("Top Contributors"),
        "instancetitle": instancetitle,
        "translationlegend": self.gettranslationsummarylegendl10n()
        }
    pagelayout.PootleNavPage.__init__(self, templatename, templatevars, request, bannerheight=80)

  def getlanguageinfo(self):
    """returns information defined for the language"""
    # specialchars = self.potree.getlanguagespecialchars(self.languagecode)
    nplurals = self.language.nplurals
    pluralequation = self.language.pluralequation
    infoparts = [(_("Language Code"), self.languagecode),
                 (_("Language Name"), tr_lang(self.languagename)),
                 # (_("Special Characters"), specialchars),
                 (_("Number of Plurals"), str(nplurals)),
                 (_("Plural Equation"), pluralequation),
                ]
    return [{"title": title, "value": value} for title, value in infoparts]

  def getprojects(self, request):
    """gets the info on the projects"""
    language_index, project_index = TranslationProject.get_language_and_project_indices()
    #self.projectcount = len(project_index)
    #translation_projects = [projects.get_translation_project(self.language, project) for project in projects_]
    #projectitems = [self.getprojectitem(translation_project) for translation_project in translation_projects
    #                if "view" in translation_project.getrights(request.user)]
    projectitems = [self.getprojectitem(translation_project)
                    for translation_project in language_index[self.language.code]]
    for n, item in enumerate(projectitems):
      item["parity"] = ["even", "odd"][n % 2]
    return projectitems

  def getprojectitem(self, translation_project):
    project = translation_project.project
    href = '%s/' % project.code
    projectdescription = shortdescription(project.description)
    projectstats = translation_project.get_quick_stats()
    projectdata = self.getstats(translation_project, translation_project.directory, None)
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
    projectstats = nlocalize("%d language, average %d%% translated", "%d languages, average %d%% translated", len(languages), len(languages), average)
    projectname = self.project.fullname
    description = self.project.description
    meta_description = shortdescription(description)
    instancetitle = pan_app.get_title()
    # l10n: The first parameter is the name of the installation
    # l10n: The second parameter is the name of the project/language
    # l10n: This is used as a page title. Most languages won't need to change this
    pagetitle =  _("%s: %s" % (instancetitle, projectname))
    templatename = "project"
    adminlink = _("Admin")
    statsheadings = self.getstatsheadings()
    statsheadings["name"] = _("Language")

    def narrow(query):
      return limit(query.filter(translation_project__project=self.project))

    topsugg    = narrow(Suggestion.objects.get_top_suggesters())
    topreview  = narrow(Suggestion.objects.get_top_reviewers())
    topsub     = narrow(Submission.objects.get_top_submitters())

    topstats = gentopstats(topsugg, topreview, topsub)

    templatevars = {"pagetitle": pagetitle,
        "project": {"code": project.code, "name": project.fullname, "stats": projectstats},
        "description": description, "meta_description": meta_description,
        "adminlink": adminlink, "languages": languages,
        "untranslatedtext": _("%s untranslated words"),
        "fuzzytext": _("%s fuzzy words"),
        "complete": _("Complete"),
        "instancetitle": instancetitle, 
        # top users
        "topstats": topstats, "topstatsheading": _("Top Contributors"),
        "statsheadings": statsheadings,
        "translationlegend": self.gettranslationsummarylegendl10n()
        }
    pagelayout.PootleNavPage.__init__(self, templatename, templatevars, request, bannerheight=80)

  def getlanguages(self, request):
    """gets the stats etc of the languages"""
    _language_index, project_index = TranslationProject.get_language_and_project_indices()
    languageitems = [self.getlanguageitem(translation_project)
                     for translation_project in project_index[self.project.code]]
    for n, item in enumerate(languageitems):
      item["parity"] = ["even", "odd"][n % 2]
    return languageitems

  def getlanguageitem(self, translation_project):
    language = translation_project.language
    href = "../../%s/%s/" % (language.code, self.projectcode)
    quickstats = translation_project.get_quick_stats()
    data = self.getstats(translation_project, translation_project.directory, None)
    self.updatepagestats(data["translatedsourcewords"], data["totalsourcewords"])
    return {"code": language.code, "icon": "language", "href": href, "title": tr_lang(language.fullname), "data": data}

def get_bool(dict_obj, name):
  if name in dict_obj:
    try:
      result = dict_obj[name]
      if result == '1':
        return True
      else:
        return False
    except KeyError:
      return False

def get_goal(args):
  try:
    return Goal.objects.get(name=args.pop('goal'))
  except:
    return None

class ProjectIndex(pagelayout.PootleNavPage):
  """The main page of a project in a specific language"""
  def __init__(self, translation_project, request, directory):
    self.translation_project = translation_project
    language = translation_project.language
    project  = translation_project.project
    self.request = request
    self.rights = translation_project.getrights(request.user)
    message = escape(request.GET.get("message", ""))
    # handle actions before generating URLs, so we strip unneccessary parameters out of argdict
    self.handleactions(request)
    # generate the navigation bar maintaining state
    directory = translation_project.directory_root
    navbarpath_dict = self.makenavbarpath_dict(project=translation_project, request=self.request,
                                               directory=directory)
    self.showchecks  = get_bool(request.GET, 'showchecks')
    self.showassigns = get_bool(request.GET, 'showassigns')
    self.showgoals   = get_bool(request.GET, 'showgoals')
    self.currentgoal = get_goal(request.GET)
    if get_bool(request.GET, 'editing'):
      actionlinks = self.getactionlinks(directory, ["editing", "mine", "review", "check", "assign", "goal", "quick", "all", "zip", "sdf"], dirfilter)
    else:
      actionlinks = self.getactionlinks(directory, ["editing", "goal", "zip", "sdf"])
    mainstats = self.getitemstats(directory, None, directory.num_stores())
    if self.showgoals:
      childitems = self.getgoalitems(directory, self.currentgoal)
    else:
      childitems = self.getchilditems(directory, self.currentgoal)
    instancetitle = pan_app.get_title()
    # l10n: The first parameter is the name of the installation (like "Pootle")
    pagetitle = _("%s: Project %s, Language %s" % (instancetitle, project.fullname, tr_lang(language.fullname)))
    templatename = "fileindex"

    def narrow(query):
      return query.filter(project=project, language=language)[:5]

    topsugg    = narrow(Suggestion.objects.get_top_suggesters())
    topreview  = narrow(Suggestion.objects.get_top_reviewers())
    topsub     = narrow(Submission.objects.get_top_submitters())

    topstats = gentopstats(topsugg, topreview, topsub)

    templatevars = {"pagetitle": pagetitle,
        "project": {"code": project.code, "name": project.fullname},
        "language": {"code": language.code, "name": tr_lang(language.fullname)},
        # optional sections, will appear if these values are replaced
        "assign": None, "goals": None, "upload": None,
        "search": {"title": _("Search"),
                   "advanced_title": _("Advanced Search"),
                   "fields": self.getsearchfields() },
        "message": message,
        # navigation bar
        "navitems": [{"icon": "folder", "path": navbarpath_dict, "actions": actionlinks, "stats": mainstats}],
        # children
        "children": childitems,
        # are we in editing mode (otherwise stats)
        "editing": get_bool(self.GET, 'editing'),
        # stats table headings
        "statsheadings": self.getstatsheadings(),
        # top users
        "topstats": topstats,
        "topstatsheading": _("Top Contributors"),
        "untranslatedtext": _("%s untranslated words"),
        "fuzzytext": _("%s fuzzy words"),
        "complete": _("Complete"),
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

  def handleactions(self, request):
    """handles the given actions that must be taken (changing operations)"""
    if request.method != 'POST':
      return

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
        raise ValueError(_("Cannot upload file, no file attached"))
      if transfiles:
        self.translation_project.uploadfile(self.request, self.dirname, uploadfile.filename, uploadfile.contents, overwrite)
        self.translation_project.scanpofiles()
      elif uploadfile.filename.endswith(".zip"):
        self.translation_project.uploadarchive(self.request, self.dirname, uploadfile.contents)
        self.translation_project.scanpofiles()
      else:
        raise ValueError(_("Can only upload PO files and zips of PO files"))
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
      "title": _("Assign Strings"),
      "action_text": _("Assign Action"),
      "users_text": _("Assign to User"),
      "button": _("Assign Strings")
    }

  def getgoalbox(self):
    """adds a box that lets the user add a new goal"""
    return {"title": _('goals'),
            "name-title": _("Enter goal name"),
            "button": _("Add Goal")}

  def getuploadbox(self):
    """adds a box that lets the user assign strings"""
    uploadbox = {
            "title": _("Upload File"),
            "file_title": _("Select file to upload"),
            "upload_button": _("Upload File")
            }
    if "admin" in self.rights or "overwrite" in self.rights:
      uploadbox.update({
            #l10n: radio button text
            "overwrite": _("Overwrite"),
            #l10n: tooltip
            "overwrite_title": _("Overwrite the current file if it exists"),
            #l10n: radio button text
            "merge": _("Merge"),
            #l10n: tooltip
            "merge_title": _("Merge the file with the current file and turn conflicts into suggestions"),
            })
    return uploadbox

  def getchilditems(self, directory, goal):
    """get all the items for directories and files viewable at this level"""
    dir_items = []
    for child_dir in directory.child_dirs.all():
      dir_items.append((child_dir.name, self.getdiritem(child_dir, goal)))
    file_items = []
    for child_store in directory.child_stores.all():
      file_items.append((child_store.name, self.getfileitem(child_store)))
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

  def getgoalitems(self, directory):
    """get all the items for directories and files viewable at this level"""
    def get_all_goals(directory):
      if directory is not None:
        return list(directory.goal_set.all()) + get_all_goals(directory.parent)
      else:
        return []

    allitems = []
    allchildren = []
    for child_dir in directory.child_dirs:
      allchildren.append(child_dir.name + os.path.sep)
    for child_store in directory.child_stores:
      allchildren.append(child_dir.name)

    # using a goal of "" means that the file has no goal
    nogoal = ""
    if self.currentgoal is None:
      goals = get_all_goals(self.translation_project.directory_root)
    else:
      goals = [self.currentgoal]
    goalfiledict = {}
    for goal in goals:
      goalfiledict[goal.name] = list(list_stores(directory, None, goal))
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

  def getgoalitem(self, goal_obj, dirfilter, goalusers):
    """returns an item showing a goal entry"""
    goal = {"actions": None, "icon": "goal", "isgoal": True, "goal": {"name": goalname}}
    if goalname:
      goal["title"] = goalname
    else:
      goal["title"] = _("Not in a goal")
    goal["href"] = self.makelink("index.html", goal=goalname)
    if pofilenames:
      actionlinks = self.getactionlinks("", linksrequired=["mine", "review", "translate", "zip"], goal=goalname)
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
        goal["goal"]["adduser_title"] = _("Add User")
    goal["stats"] = self.getitemstats("", pofilenames, len(pofilenames), {'goal': goalname})
    projectstats = self.translation_project.getquickstats(goal_obj)
    goal["data"] = self.getstats(self.translation_project, projectstats)
    return goal

  def getdiritem(self, directory, goal, linksrequired=None, **newargs):
    """returns an item showing a directory entry"""
    browseurl = self.getbrowseurl("%s" % directory.pootle_path, **newargs)
    diritem = {"href": browseurl, "title": directory.pootle_path, "icon": "folder", "isdir": True}
    actionlinks = self.getactionlinks(directory, linksrequired=linksrequired)
    diritem["actions"] = actionlinks
    
    if self.showgoals and "goal" in self.request.GET:
      diritem["stats"] = self.getitemstats(directory, self.currentgoal, (directory.num_stores(self.currentgoal), directory.num_stores()))
    else:
      diritem["stats"] = self.getitemstats(directory, self.currentgoal, directory.num_stores())

    diritem["data"] = self.getstats(self.translation_project, directory, goal)
    return diritem

  def getfileitem(self, store, linksrequired=None, **newargs):
    """returns an item showing a file entry"""
    if linksrequired is None:
      if store.name.endswith('.po'):
        linksrequired = ["mine", "review", "quick", "all", "po", "xliff", "ts", "csv", "mo", "update", "commit"]
      else:
        linksrequired = ["mine", "review", "quick", "all", "po", "xliff", "update", "commit"]
    browseurl = self.getbrowseurl(store.name, **newargs)
    fileitem = {"href": browseurl, "title": store.name, "icon": "file", "isfile": True}
    actions = self.getactionlinks(store, linksrequired=linksrequired)
    actionlinks = actions["extended"]
    if "po" in linksrequired:
      poname = store.name.replace(".xlf", ".po")
      polink = {"href": poname, "text": _('PO file')}
      actionlinks.append(polink)
    if "xliff" in linksrequired and "translate" in self.rights:
      xliffname = store.name.replace(".po", ".xlf")
      xlifflink = {"href": xliffname, "text": _('XLIFF file')}
      actionlinks.append(xlifflink)
    if "ts" in linksrequired and "translate" in self.rights:
      tsname = store.name.replace(".po", ".ts")
      tslink = {"href": tsname, "text": _('Qt .ts file')}
      actionlinks.append(tslink)
    if "csv" in linksrequired and "translate" in self.rights:
      csvname = store.name.replace(".po", ".csv")
      csvlink = {"href": csvname, "text": _('CSV file')}
      actionlinks.append(csvlink)
    if "mo" in linksrequired:
      if self.translation_project.db_translation_project.project.createmofiles and "pocompile" in self.rights:
        moname = store.name.replace(".po", ".mo")
        molink = {"href": moname, "text": _('MO file')}
        actionlinks.append(molink)
    if "update" in linksrequired and "admin" in self.rights:
      if versioncontrol.hasversioning(os.path.join(self.translation_project.podir,
              self.dirname, store.name)):
        # l10n: Update from version control (like CVS or Subversion)
        updatelink = {"href": "index.html?editing=1&doupdate=1&updatefile=%s" % (store.name), "text": _('Update')}
        actionlinks.append(updatelink)
    if "commit" in linksrequired and "commit" in self.rights:
      if versioncontrol.hasversioning(os.path.join(self.translation_project.podir,
              self.dirname, store.name)):
        # l10n: Commit to version control (like CVS or Subversion)
        commitlink = {"href": "index.html?editing=1&docommit=1&commitfile=%s" % (store.name), "text": _('Commit')}
        actionlinks.append(commitlink)
    # update the separators
    for n, actionlink in enumerate(actionlinks):
      if n < len(actionlinks)-1:
        actionlink["sep"] = " | "
      else:
        actionlink["sep"] = ""
    fileitem["actions"] = actions
    fileitem["stats"] = self.getitemstats(store, None, 1)
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
      assignwhich = [('all', _("All Strings")),
                     ('untranslated', _("Untranslated")),
                     ('unassigned', _('Unassigned')),
                     ('unassigneduntranslated', _("Unassigned and Untranslated"))]
    return {
     "name": goalformname,
     "filename": basename,
     "goalnames": goalnames,
     "filegoals": dict([(goalname, goalname in filegoals or None) for goalname in goalnames]),
     "multifiles": multifiles,
     "setgoal_text": _("Set Goal"),
     "users": useroptions,
     "assignusers": dict([(username, username in assignusers or None) for username in useroptions]),
     "multiusers": multiusers,
     "selectmultiple_text": _("Select Multiple"),
     "assignwhich": [{"value": value, "text": text} for value, text in assignwhich],
     "assignto_text": _("Assign To"),
     }

  def getactionlinks(self, path_obj, linksrequired=None, filepath=None, goal=None):
    """get links to the actions that can be taken on an item (directory / file)"""
    if linksrequired is None:
      linksrequired = ["mine", "review", "quick", "all"]
    actionlinks = []
    actions = {}
    actions["goalform"] = None
    stats_totals   = path_obj.get_stats_totals(self.translation_project.checker)
    if isinstance(path_obj, Directory):
      baseactionlink = path_obj.pootle_path + "translate.html?"
      baseindexlink = path_obj.pootle_path + "index.html?"
    else:
      baseactionlink = "%s?translate=1" % path_obj.pootle_path
      baseindexlink = "%s?index=1" % path_obj.pootle_path
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
    addoptionlink("editing", None, "editing", _("Show Editing Functions"),
                                              _("Show Statistics"))
    # l10n: "Checks" are quality checks that Pootle performs on translations to test for common mistakes
    addoptionlink("check", "translate", "showchecks", _("Show Checks"), _("Hide Checks"))
    addoptionlink("goal", None, "showgoals", _("Show Goals"), _("Hide Goals"))
    addoptionlink("assign", "translate", "showassigns", _("Show Assigns"), _("Hide Assigns"))
    actions["basic"] = actionlinks
    actionlinks = []
    if not goal:
      filegoals = self.translation_project.getfilegoals(path_obj.pootle_path)
      if self.showgoals:
        if len(filegoals) > 1:
          #TODO: This is not making sense. For now make it an unclickable link
          allgoalslink = {"href": "", "text": _("All Goals: %s" % ", ".join(filegoals))}
          actionlinks.append(allgoalslink)
      if "editgoal" in linksrequired and "admin" in self.rights:
        actions["goalform"] = self.getgoalform(basename, goalfile, filegoals)
    if "mine" in linksrequired and not self.request.user.is_anonymous:
      if "translate" in self.rights:
        minelink = _("Translate My Strings")
      else:
        minelink = _("View My Strings")
      mystats = stats.assign.get(self.request.user.username, [])
      if len(mystats):
        minelink = {"href": self.makelink(baseactionlink, assignedto=self.request.user.username), "text": minelink}
      else:
        minelink = {"title": _("No strings assigned to you"), "text": minelink}
      actionlinks.append(minelink)
      if "quick" in linksrequired and "translate" in self.rights:
        if len(mystats) > 0: # A little shortcut to avoid the call to projectstats.units if we don't have anything assigned
          mytranslatedstats = [statsitem for statsitem in mystats if statsitem in stats.units.get("translated", [])]
        else:
          mytranslatedstats = []
        quickminelink = _("Quick Translate My Strings")
        if len(mytranslatedstats) < len(mystats):
          quickminelink = {"href": self.makelink(baseactionlink, assignedto=self.request.user.username, fuzzy=1, untranslated=1), "text": quickminelink}
        else:
          quickminelink = {"title": _("No untranslated strings assigned to you"), "text": quickminelink}
        actionlinks.append(quickminelink)
    if "review" in linksrequired and stats_totals.get("check-hassuggestion", 0):
      if "review" in self.rights:
        reviewlink = _("Review Suggestions")
      else:
        reviewlink = _("View Suggestions")
      reviewlink = {"href": self.makelink(baseactionlink, review=1, **{"hassuggestion": 1}), "text": reviewlink}
      actionlinks.append(reviewlink)
    if "quick" in linksrequired:
      if "translate" in self.rights:
        quicklink = _("Quick Translate")
      else:
        quicklink = _("View Untranslated")
      if stats_totals['translated'] < stats_totals['total']:
        quicklink = {"href": self.makelink(baseactionlink, fuzzy=1, untranslated=1), "text": quicklink}
      else:
        quicklink = {"title": _("No untranslated items"), "text": quicklink}
      actionlinks.append(quicklink)
    if "all" in linksrequired and "translate" in self.rights:
      translatelink = {"href": self.makelink(baseactionlink), "text": _('Translate All')}
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
        linktext = _('ZIP of goal')
      else:
        linktext = _('ZIP of folder')
      ziplink = {"href": archivename, "text": linktext, "title": archivename}
      actionlinks.append(ziplink)

    if "sdf" in linksrequired and "pocompile" in self.rights and \
        self.translation_project.ootemplate() and not (basename or filepath):
      archivename = self.translation_project.languagecode + ".sdf"
      linktext = _('Generate SDF')
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

  def getitemstats(self, path_obj, goal, numfiles, url_opts={}):
    """returns a widget summarizing item statistics"""
    stats = {"summary": self.describestats(self.translation_project,
                                           path_obj,
                                           goal,
                                           numfiles), "checks": [], "tracks": [], "assigns": []}
    if isinstance(path_obj, Directory):
      linkbase = path_obj.pootle_path + "translate.html?"
    else:
      linkbase = path_obj.pootle_path + "?translate=1"
    if self.showchecks:
      stats["checks"] = self.getcheckdetails(path_obj, goal, linkbase, url_opts)
    if self.showassigns:
      if not basename or basename.endswith("/"):
        removelinkbase = "?showassigns=1&removeassigns=1"
      else:
        removelinkbase = "?showassigns=1&removeassigns=1&removefilter=%s" % basename
      stats["assigns"] = self.getassigndetails(path_obj, linkbase, removelinkbase)
    return stats

  def gettrackdetails(self, projecttracks, linkbase):
    """return a list of strings describing the results of tracks"""
    return [trackmessage for trackmessage in projecttracks]

  def getcheckdetails(self, path_obj, goal, linkbase, url_opts={}):
    """return a list of strings describing the results of checks"""
    property_stats = path_obj.get_property_stats(self.translation_project.checker, goal)
    total = len(property_stats['total'])
    checklinks = []
    keys = stats.keys()
    keys.sort()
    for checkname in keys:
      if not checkname.startswith("check-"):
        continue
      checkcount = len(property_stats[checkname])
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
        stats = _("%d/%d words (%d%%) assigned" % (assignwords, totalwords, percentassigned))
        stringstats = _("[%d/%d strings]" % (assigncount, totalcount))
        completestats = _("%d/%d words (%d%%) translated" % (completewords, assignwords, percentcomplete))
        completestringstats = _("[%d/%d strings]" % (completecount, assigncount))
        if "assign" in self.rights:
          removetext = _("Remove")
          removelink = {"href": self.makelink(removelinkbase, assignedto=assignname), "text": removetext}
        else:
          removelink = None
        assignlinks.append({"assign": assignlink, "stats": stats, "stringstats": stringstats, "completestats": completestats, "completestringstats": completestringstats, "remove": removelink})
    return assignlinks


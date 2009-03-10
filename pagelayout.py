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

import os

from django.conf import settings
from django.utils.html import escape
from django.utils.translation import ugettext as _

from pootle_app.fs_models import FakeSearch
from pootle_app.profile import get_profile

from Pootle import pan_app
from Pootle.i18n.jtoolkit_i18n import nlocalize, tr_lang
from Pootle.i18n import gettext

def localize_links(request):
  """Localize all the generic links"""
  links = {}
  links["home"] = _("Home")
  links["projects"] = _("All projects")
  links["languages"] = _("All languages")
  links["account"] = _("My account")
  links["admin"] = _("Admin")
  links["doc"] = _("Help")
  links["doclang"] = getdoclang(gettext.get_active().language.code)
  links["logout"] = _("Log out")
  links["login"] = _("Log in")
  links["about"] = _("About")
  #l10n: Verb, as in "to register"
  links["register"] = _("Register")
  links["activate"] = _("Activate")

  # accessibility links
  links["skip_nav"] = _("skip to navigation")
  links["switch_language"] = _("switch language")

  return links

def getdoclang(language):
  """Get the language code that the docs should be displayed in."""

  #TODO: Determine the available languages programmatically.
  available_languages = ["en"]
  if language in available_languages:
    return language
  else:
    return "en"

def languagedir(language):
  """Returns whether the language is right to left"""
  shortcode = language[:3]
  if not shortcode.isalpha():
    shortcode = language[:2]
  if shortcode in ["ar", "arc", "dv", "fa", "he", "ks", "ps", "ur", "yi"]:
    return "rtl"
  return "ltr"

def weblanguage(language):
  """Reformats the language code from locale style (pt_BR) to web style (pt-br)"""
  return language.replace("_", "-")

def localelanguage(language):
  """Reformats the language code from web style (pt-br) to locale style (pt_BR)"""
  dashindex = language.find("-")
  if dashindex >= 0:
    language = language[:dashindex] + "_" + language[dashindex+1:].upper()
  return language

def completetemplatevars(templatevars, request, bannerheight=135):
  """fill out default values for template variables"""
  if not "instancetitle" in templatevars:
    templatevars["instancetitle"] = settings.TITLE
  templatevars["sessionvars"] = {
      "status": get_profile(request.user).status,
      "isopen": request.user.is_authenticated(),
      "issiteadmin": request.user.is_superuser}
  templatevars["request"] = request
  if not "unlocalizedurl" in templatevars:
    templatevars["unlocalizedurl"] = settings.BASE_URL
    if not templatevars["unlocalizedurl"].endswith("/"):
    	templatevars["unlocalizedurl"] += "/"
  if not "baseurl" in templatevars:
    templatevars["baseurl"] = getattr(request, "localizedurl", "/")
    if not templatevars["baseurl"].endswith("/"):
    	templatevars["baseurl"] += "/"
  if not "mediaurl" in templatevars:
    templatevars["mediaurl"] = settings.MEDIA_URL
  if not "enablealtsrc" in templatevars:
     templatevars["enablealtsrc"] = settings.ENABLE_ALT_SRC
  templatevars["aboutlink"] = _("About this Pootle server")
  templatevars["uilanguage"] = weblanguage(gettext.get_active().language.code)
  templatevars["uidir"] = languagedir(gettext.get_active().language.code)
  # TODO FIXME cssaligndir is deprecated?
  if templatevars["uidir"] == 'ltr':  
    templatevars["cssaligndir"] = "left"
  else:
    templatevars["cssaligndir"] = "right"
  templatevars["username_title"] = _("Username")
  try:
    templatevars["username"] = templatevars["username"]
  except:
    templatevars["username"] = "" 
  templatevars["password_title"] = _("Password")
  templatevars["login_text"] = _('Log in')
  templatevars["logout_text"] = _('Log out')
  templatevars["register_text"] = _('Register')
  templatevars["canregister"] = settings.CAN_REGISTER
  templatevars["links"] = localize_links(request)
  templatevars["current_url"] = request.path_info
  if "?" in request.path_info: 
    templatevars["logout_link"] = request.path_info+"&islogout=1"
  else:
    templatevars["logout_link"] = request.path_info+"?islogout=1"
  if "user" not in templatevars:
    templatevars["user"] = request.user
  if "search" not in templatevars:
    templatevars["search"] = None

  templatevars['message'] = escape(request.GET.get('message', ''))

class PootlePage:
  """the main page"""
  def __init__(self, templatename, templatevars, request, bannerheight=135):
    self.request = request
    self.templatename = templatename
    self.templatevars = templatevars
    self.completevars(bannerheight)

  def completevars(self, bannerheight=135):
    """fill out default values for template variables"""
    if hasattr(self, "templatevars"):
      completetemplatevars(self.templatevars, self.request, bannerheight=bannerheight)

  def polarizeitems(self, itemlist):
    """take an item list and alternate the background colour"""
    polarity = False
    for n, item in enumerate(itemlist):
      if isinstance(item, dict):
        item["parity"] = ["even", "odd"][n % 2]
      else:
        item.setpolarity(polarity)
      polarity = not polarity
    return itemlist
  
  def gettranslationsummarylegendl10n(self):
    """Returns a dictionary of localized headings.  This is only used because we
    can't do L10n directly in our templates. :("""
    headings = {"translated":   _("Translations are complete"),
                "fuzzy":        _("Translations need to be checked (they are marked fuzzy)"),
                "untranslated": _("Untranslated") }
    return headings

def get_relative(ref_path, abs_path):
  ref_chain = ref_path.split('/')
  abs_chain = abs_path.split('/')
  abs_set = dict((component, i) for i, component in enumerate(abs_path.split('/')))
  for i, component in enumerate(reversed(ref_chain)):
    if component in abs_set:
      new_components = i * ['..']
      new_components.extend(abs_chain[abs_set[component]+1:])
      return '/'.join(new_components)

class PootleNavPage(PootlePage):
  def makenavbarpath_dict(self, project=None, request=None, directory=None, language=None, store=None):
    """create the navbar location line"""
    #FIXME: Still lots of PO specific references here!
    project_path = get_relative(request.path_info, project.directory_root.pootle_path)
    rootlink = ""
    paramstring = ""
    if request:
      paramstring = "?" + "&".join(["%s=%s" % (arg, value) for arg, value in request.GET.iteritems() 
                                    if arg.startswith("show") or arg == "editing"])

    links = {"admin": None, "project": [], "language": [], "goal": [], "pathlinks": []}

    pathlinks = []
    for ancestor_directory in directory.parent_chain():
      pathlinks.append({"href": self.getbrowseurl(get_relative(request.path_info, ancestor_directory.pootle_path)), 
                        "text": ancestor_directory.name, "sep": " / "})
    if pathlinks:
      pathlinks[-1]["sep"] = ""
    links["pathlinks"] = pathlinks

    if request and "goal" in request.GET:
      # goallink = {"href": self.getbrowseurl("", goal=goal), "text": goal}
      links["goal"] = {"href": self.getbrowseurl(""), "text": _("All goals")}
    if project:
      if isinstance(project, tuple):
        projectcode, projectname = project
        links["project"] = {"href": "/projects/%s/%s" % (projectcode, paramstring), "text": projectname}
      else:
        links["language"] = {"href": project_path + "../index.html", "text": tr_lang(project.languagename)}
        # don't getbrowseurl on the project link, so sticky options won't apply here
        links["project"] = {"href": project_path + paramstring, "text": project.projectname}
        if request:
          if "admin" in project.getrights(request.user) or request.user.is_superuser:
            links["admin"] = {"href": project_path + "admin.html", "text": _("Admin")}
    elif language:
      languagecode, languagename = language
      links["language"] = {"href": "/%s/" % languagecode, "text": tr_lang(languagename)}
    return links

  def getbrowseurl(self, basename, **newargs):
    """gets the link to browse the item"""
    if not basename or basename.endswith("/"):
      return self.makelink(basename or "index.html", **newargs)
    else:
      return self.makelink(basename, translate=1, view=1, **newargs)

  def makelink(self, link, **newargs):
    """constructs a link that keeps sticky arguments e.g. showchecks"""
    combinedargs = self.request.GET.copy()
    combinedargs.update(newargs)
    if '?' in link:
      if not (link.endswith("&") or link.endswith("?")):
        link += "&"
    else:
      link += '?'
    # TODO: check escaping
    link += "&".join(["%s=%s" % (arg, value) for arg, value in combinedargs.iteritems() if arg != "allowmultikey"])
    return link

  def initpagestats(self):
    """initialise the top level (language/project) stats"""
    self.alltranslated = 0
    self.grandtotal = 0
    
  def getpagestats(self):
    """return the top level stats"""
    return (self.alltranslated*100/max(self.grandtotal, 1))

  def updatepagestats(self, translated, total):
    """updates the top level stats"""
    self.alltranslated += translated
    self.grandtotal += total

  def describestats(self, translation_project, directory, goal, numfiles):
    """returns a sentence summarizing item statistics"""
    quick_stats = directory.get_quick_stats(translation_project.checker, goal)
    percentfinished = (quick_stats['translatedsourcewords']*100/max(quick_stats['totalsourcewords'], 1))
    if isinstance(numfiles, tuple):
      filestats = _("%d/%d file" % numfiles) + ", "
    else:
      filestats = nlocalize("%d file", "%d files", numfiles, numfiles) + ", "
    wordstats = _("%d/%d words (%d%%) translated" %
                  (quick_stats['translatedsourcewords'],
                  quick_stats['totalsourcewords'],
                  percentfinished))
    stringstatstext = _("%d/%d strings" % (quick_stats['translated'], quick_stats['total']))
    stringstats = ' <span class="string-statistics">[%s]</span>' % stringstatstext
    return filestats + wordstats + stringstats

  def getstatsheadings(self):
    """returns a dictionary of localised headings"""
    headings = {"name": _("Name"),
                "translated": _("Translated"),
                "translatedpercentage": _("Translated percentage"),
                "translatedwords": _("Translated words"),
                "fuzzy": _("Fuzzy"),
                "fuzzypercentage": _("Fuzzy percentage"),
                "fuzzywords": _("Fuzzy words"),
                "untranslated": _("Untranslated"),
                "untranslatedpercentage": _("Untranslated percentage"),
                "untranslatedwords": _("Untranslated words"),
                "total": _("Total"),
                "totalwords": _("Total words"),
                # l10n: noun. The graphical representation of translation status
                "progress": _("Progress"),
                "summary": _("Summary")}
    return headings

  def getstats(self, project, directory, goal):
    """returns a list with the data items to fill a statistics table
    Remember to update getstatsheadings() above as needed"""
    wanted = ["translated", "fuzzy", "total"]
    gotten = {}
    stats_totals = directory.get_stats_totals(project.checker, FakeSearch(goal))
    for key in wanted:
      gotten[key] = stats_totals.get(key, 0)
      wordkey = key + "sourcewords"
      gotten[wordkey] = stats_totals[wordkey]

    gotten["untranslated"] = gotten["total"] - gotten["translated"] - gotten["fuzzy"]
    gotten["untranslatedsourcewords"] = gotten["totalsourcewords"] - gotten["translatedsourcewords"] - gotten["fuzzysourcewords"]

    wanted = ["translated", "fuzzy", "untranslated"]
    for key in wanted:
      percentkey = key + "percentage"
      wordkey = key + "sourcewords"
      gotten[percentkey] = int(gotten[wordkey]*100/max(gotten["totalsourcewords"], 1))

    for key in gotten:
      if key.find("check-") == 0:
        value = gotten.pop(key)
        gotten[key[len("check-"):]] = value

    return gotten

  def getsearchfields(self):
    source    = self.request.GET.get('source', '0')
    target    = self.request.GET.get('target', '0')
    notes     = self.request.GET.get('notes', '0')
    locations = self.request.GET.get('locations', '0')
    tmpfields = [{"name":    "source",
                  "text":    _("Source Text"),
                  "value":   source,
                  "checked": source == "1" and "checked" or None},
                 {"name":    "target",
                  "text":    _("Target Text"),
                  "value":   target,
                  "checked": target == "1" and "checked" or None},
                 {"name":    "notes",
                  "text":    _("Comments"),
                  "value":   notes,
                  "checked": notes == "1" and "checked" or None},
                 {"name":    "locations",
                  "text":    _("Locations"),
                  "value":   locations,
                  "checked": locations == "1" and "checked" or None}]

    selection = [bool(field["checked"]) for field in tmpfields]
    if selection == [True, True, False, False]:
      # use only the default css class for the search form
      self.extra_class = False
    elif selection == [False, False, False, False]:
      # no search field selected - we use the default instead
      tmpfields[0]["checked"] = "checked"
      tmpfields[1]["checked"] = "checked"
      self.extra_class = False
    else:
      # add an extra css class to the search form
      self.extra_class = True

    return tmpfields


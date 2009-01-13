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

from Pootle import pan_app
from pootle_app.models import get_profile
from Pootle.i18n.jtoolkit_i18n import localize, nlocalize, tr_lang
from Pootle.i18n import gettext

def localize_links(request):
  """Localize all the generic links"""
  links = {}
  links["home"] = localize("Home")
  links["projects"] = localize("All projects")
  links["languages"] = localize("All languages")
  links["account"] = localize("My account")
  links["admin"] = localize("Admin")
  links["doc"] = localize("Docs & help")
  links["doclang"] = getdoclang(gettext.get_active().languagecode)
  #links["logout"] = localize("Log out")
  #links["login"] = localize("Log in")
  links["about"] = localize("About")
  #l10n: Verb, as in "to register"
  links["register"] = localize("Register")
  links["activate"] = localize("Activate")

  # accessibility links
  links["skip_nav"] = localize("skip to navigation")
  links["switch_language"] = localize("switch language")

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
    templatevars["instancetitle"] = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
  templatevars["sessionvars"] = {
      "status": get_profile(request.user).status,
      "isopen": request.user.is_authenticated(),
      "issiteadmin": request.user.is_superuser}
  templatevars["request"] = request
  if not "unlocalizedurl" in templatevars:
    templatevars["unlocalizedurl"] = getattr(pan_app.prefs, "baseurl", "/")
    if not templatevars["unlocalizedurl"].endswith("/"):
    	templatevars["unlocalizedurl"] += "/"
  if not "baseurl" in templatevars:
    templatevars["baseurl"] = getattr(request, "localizedurl", "/")
    if not templatevars["baseurl"].endswith("/"):
    	templatevars["baseurl"] += "/"
  if not "enablealtsrc" in templatevars:
     templatevars["enablealtsrc"] = getattr(pan_app.prefs, "enablealtsrc", False)
  templatevars["aboutlink"] = localize("About this Pootle server")
  templatevars["uilanguage"] = weblanguage(gettext.get_active().languagecode)
  templatevars["uidir"] = languagedir(gettext.get_active().languagecode)
  # TODO FIXME cssaligndir is deprecated?
  if templatevars["uidir"] == 'ltr':  
    templatevars["cssaligndir"] = "left"
  else:
    templatevars["cssaligndir"] = "right"
  templatevars["username_title"] = localize("Username")
  try:
    templatevars["username"] = templatevars["username"]
  except:
    templatevars["username"] = "" 
  templatevars["password_title"] = localize("Password")
  templatevars["login_text"] = localize('Log in')
  templatevars["logout_text"] = localize('Log out')
  templatevars["register_text"] = localize('Register')
  templatevars["canregister"] = hasattr(pan_app.prefs, "hash")
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

  # Messaging system
  if "message" not in templatevars or len(templatevars['message']) == 0:
    templatevars['message'] = ''
  else:
    templatevars['message'] = templatevars['message'] + '<br />'
  for message in get_profile(request.user).get_messages():
    templatevars['message'] = templatevars['message'] + message + '<br />'

class PootlePage:
  """the main page"""
  def __init__(self, templatename, templatevars, request, bannerheight=135):
    if not hasattr(pan_app.prefs, "baseurl"):
      pan_app.prefs.baseurl = "/"
    if not hasattr(pan_app.prefs, "enablealtsrc"):
      pan_app.prefs.enablealtsrc = False
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
    headings = {"translated":     localize("Translations are complete"),
                "fuzzy":        localize("Translations need to be checked (they are marked fuzzy)"),
                "untranslated": localize("Untranslated") }
    return headings


class PootleNavPage(PootlePage):
  def makenavbarpath_dict(self, project=None, request=None, currentfolder=None, language=None, argdict=None, dirfilter=None):
    """create the navbar location line"""
    #FIXME: Still lots of PO specific references here!
    rootlink = ""
    paramstring = ""
    if argdict:
      paramstring = "?" + "&".join(["%s=%s" % (arg, value) for arg, value in argdict.iteritems() if arg.startswith("show") or arg == "editing"])

    links = {"admin": None, "project": [], "language": [], "goal": [], "pathlinks": []}
    if currentfolder:
      pathlinks = []
      dirs = currentfolder.split(os.path.sep)
      if dirfilter is None:
        dirfilter = currentfolder
      
      depth = dirfilter.count(os.path.sep) + 1
      if dirfilter == "":
        depth -= 1
      elif dirfilter.endswith(".po") or dirfilter.endswith(".xlf"):
        depth = depth - 1

      rootlink = "/".join([".."] * depth)
      if rootlink:
        rootlink += "/"
      backlinks = ""
      for backlinkdir in dirs:
        if depth >= 0:
          backlinks = "../" * depth + backlinkdir
          depth -= 1
        else:
          backlinks += backlinkdir
        if not (backlinkdir.endswith(".po") or backlinkdir.endswith(".xlf")) and not backlinks.endswith("/"):
          backlinks = backlinks + "/"
        pathlinks.append({"href": self.getbrowseurl(backlinks), "text": backlinkdir, "sep": " / "})
      if pathlinks:
        pathlinks[-1]["sep"] = ""
      links["pathlinks"] = pathlinks
    if argdict and "goal" in argdict:
      # goallink = {"href": self.getbrowseurl("", goal=goal), "text": goal}
      links["goal"] = {"href": self.getbrowseurl(""), "text": localize("All goals")}
    if project:
      if isinstance(project, tuple):
        projectcode, projectname = project
        links["project"] = {"href": "/projects/%s/%s" % (projectcode, paramstring), "text": projectname}
      else:
        links["language"] = {"href": rootlink + "../index.html", "text": tr_lang(project.languagename)}
        # don't getbrowseurl on the project link, so sticky options won't apply here
        links["project"] = {"href": (rootlink or "index.html") + paramstring, "text": project.projectname}
        if request:
          if "admin" in project.getrights(request) or request.user.is_superuser:
            links["admin"] = {"href": rootlink + "admin.html", "text": localize("Admin")}
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
    combinedargs = self.argdict.copy()
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

  def describestats(self, project, projectstats, numfiles):
    """returns a sentence summarizing item statistics"""
    translated = projectstats.get("translated", [])
    total = projectstats.get("total", 0)
    if "translatedsourcewords" in projectstats:
      translatedwords = projectstats["translatedsourcewords"]
    else:
      translatedwords = project.countwords(translated)
    totalwords = projectstats["totalsourcewords"]
    if isinstance(translated, list):
      translated = len(translated)
    if isinstance(total, list):
      total = len(total)
    percentfinished = (translatedwords*100/max(totalwords, 1))
    if numfiles is None:
      filestats = ""
    elif isinstance(numfiles, tuple):
      filestats = localize("%d/%d files", numfiles) + ", "
    else:
      #TODO: Perhaps do better?
      filestats = nlocalize("%d file", "%d files", numfiles, numfiles) + ", "
    wordstats = localize("%d/%d words (%d%%) translated", translatedwords, totalwords, percentfinished)
    stringstatstext = localize("%d/%d strings", translated, total)
    stringstats = ' <span class="string-statistics">[%s]</span>' % stringstatstext
    return filestats + wordstats + stringstats

  def getstatsheadings(self):
    """returns a dictionary of localised headings"""
    headings = {"name": localize("Name"),
                "translated": localize("Translated"),
                "translatedpercentage": localize("Translated percentage"),
                "translatedwords": localize("Translated words"),
                "fuzzy": localize("Fuzzy"),
                "fuzzypercentage": localize("Fuzzy percentage"),
                "fuzzywords": localize("Fuzzy words"),
                "untranslated": localize("Untranslated"),
                "untranslatedpercentage": localize("Untranslated percentage"),
                "untranslatedwords": localize("Untranslated words"),
                "total": localize("Total"),
                "totalwords": localize("Total words"),
                # l10n: noun. The graphical representation of translation status
                "progress": localize("Progress"),
                "summary": localize("Summary")}
    return headings

  def getstats(self, project, projectstats):
    """returns a list with the data items to fill a statistics table
    Remember to update getstatsheadings() above as needed"""
    wanted = ["translated", "fuzzy", "total"]
    gotten = {}
    for key in wanted:
      gotten[key] = projectstats.get(key, [])
      wordkey = key + "sourcewords"
      if wordkey in projectstats:
        gotten[wordkey] = projectstats[wordkey]
      else:
        count = projectstats.get(key, [])
        gotten[wordkey] = project.countwords(count)
      if isinstance(gotten[key], list):
        #TODO: consider carefully:
        gotten[key] = len(gotten[key])

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
    tmpfields = [{"name": "source",
                  "text": localize("Source Text"),
                  "value": self.argdict.get("source", 0),
                  "checked": self.argdict.get("source", 0) == "1" and "checked" or None},
                 {"name": "target",
                  "text": localize("Target Text"),
                  "value": self.argdict.get("target", 0),
                  "checked": self.argdict.get("target", 0) == "1" and "checked" or None},
                 {"name": "notes",
                  "text": localize("Comments"),
                  "value": self.argdict.get("notes", 0),
                  "checked": self.argdict.get("notes", 0) == "1" and "checked" or None},
                 {"name": "locations",
                  "text": localize("Locations"),
                  "value": self.argdict.get("locations", 0),
                  "checked": self.argdict.get("locations", 0) == "1" and "checked" or None}]

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


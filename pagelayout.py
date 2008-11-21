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

def localize_links(session):
  """Localize all the generic links"""
  links = {}
  links["home"] = session.localize("Home")
  links["projects"] = session.localize("All projects")
  links["languages"] = session.localize("All languages")
  links["account"] = session.localize("My account")
  links["admin"] = session.localize("Admin")
  links["doc"] = session.localize("Docs & help")
  links["doclang"] = getdoclang(session.language)
  #links["logout"] = session.localize("Log out")
  #links["login"] = session.localize("Log in")
  links["about"] = session.localize("About")
  #l10n: Verb, as in "to register"
  links["register"] = session.localize("Register")
  links["activate"] = session.localize("Activate")

  # accessibility links
  links["skip_nav"] = session.localize("skip to navigation")
  links["switch_language"] = session.localize("switch language")

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

def completetemplatevars(templatevars, session, bannerheight=135):
  """fill out default values for template variables"""
  if not "instancetitle" in templatevars:
    templatevars["instancetitle"] = getattr(session.instance, "title", session.localize("Pootle Demo"))
  if not "session" in templatevars:
    templatevars["session"] = {"status": session.status, "isopen": session.isopen, "issiteadmin": session.issiteadmin()}
  if not "unlocalizedurl" in templatevars:
    templatevars["unlocalizedurl"] = getattr(session.instance, "baseurl", "/")
    if not templatevars["unlocalizedurl"].endswith("/"):
    	templatevars["unlocalizedurl"] += "/"
  if not "baseurl" in templatevars:
    templatevars["baseurl"] = getattr(session, "localizedurl", "/")
    if not templatevars["baseurl"].endswith("/"):
    	templatevars["baseurl"] += "/"
  if not "enablealtsrc" in templatevars:
     templatevars["enablealtsrc"] = getattr(session.instance, "enablealtsrc", False)
  templatevars["aboutlink"] = session.localize("About this Pootle server")
  templatevars["uilanguage"] = weblanguage(session.language)
  templatevars["uidir"] = languagedir(session.language)
  # TODO FIXME cssaligndir is deprecated?
  if templatevars["uidir"] == 'ltr':  
    templatevars["cssaligndir"] = "left"
  else:
    templatevars["cssaligndir"] = "right"
  templatevars["username_title"] = session.localize("Username")
  try:
    templatevars["username"] = templatevars["username"]
  except:
    templatevars["username"] = "" 
  templatevars["password_title"] = session.localize("Password")
  templatevars["login_text"] = session.localize('Log in')
  templatevars["logout_text"] = session.localize('Log out')
  templatevars["register_text"] = session.localize('Register')
  templatevars["canregister"] = hasattr(session.instance, "hash")
  templatevars["links"] = localize_links(session)
  templatevars["current_url"] = session.currenturl
  if "?" in session.currenturl: 
    templatevars["logout_link"] = session.currenturl+"&islogout=1"
  else:
    templatevars["logout_link"] = session.currenturl+"?islogout=1"
  if "user" not in templatevars:
    templatevars["user"] = session.user
  if "search" not in templatevars:
    templatevars["search"] = None

  # Messaging system
  if "message" not in templatevars or len(templatevars['message']) == 0:
    templatevars['message'] = ''
  else:
    templatevars['message'] = templatevars['message'] + '<br />'
  for message in session.getMessages():
    templatevars['message'] = templatevars['message'] + message + '<br />'


class PootlePage:
  """the main page"""
  def __init__(self, templatename, templatevars, session, bannerheight=135):
    if not hasattr(session.instance, "baseurl"):
      session.instance.baseurl = "/"
    if not hasattr(session.instance, "enablealtsrc"):
      session.instance.enablealtsrc = False
    self.localize = session.localize
    self.session = session
    self.templatename = templatename
    self.templatevars = templatevars
    self.completevars(bannerheight)

  def completevars(self, bannerheight=135):
    """fill out default values for template variables"""
    if hasattr(self, "templatevars"):
      completetemplatevars(self.templatevars, self.session, bannerheight=bannerheight)

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
    headings = {"translated":     self.localize("Translations are complete"),
                "fuzzy":        self.localize("Translations need to be checked (they are marked fuzzy)"),
                "untranslated": self.localize("Untranslated") }
    return headings


class PootleNavPage(PootlePage):
  def makenavbarpath_dict(self, project=None, session=None, currentfolder=None, language=None, argdict=None, dirfilter=None):
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
      links["goal"] = {"href": self.getbrowseurl(""), "text": self.localize("All goals")}
    if project:
      if isinstance(project, tuple):
        projectcode, projectname = project
        links["project"] = {"href": "/projects/%s/%s" % (projectcode, paramstring), "text": projectname}
      else:
        links["language"] = {"href": rootlink + "../index.html", "text": session.tr_lang(project.languagename)}
        # don't getbrowseurl on the project link, so sticky options won't apply here
        links["project"] = {"href": (rootlink or "index.html") + paramstring, "text": project.projectname}
        if session:
          if "admin" in project.getrights(session) or session.issiteadmin():
            links["admin"] = {"href": rootlink + "admin.html", "text": self.localize("Admin")}
    elif language:
      languagecode, languagename = language
      links["language"] = {"href": "/%s/" % languagecode, "text": session.tr_lang(languagename)}
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
      filestats = self.localize("%d/%d files", numfiles) + ", "
    else:
      #TODO: Perhaps do better?
      filestats = self.nlocalize("%d file", "%d files", numfiles, numfiles) + ", "
    wordstats = self.localize("%d/%d words (%d%%) translated", translatedwords, totalwords, percentfinished)
    stringstatstext = self.localize("%d/%d strings", translated, total)
    stringstats = ' <span class="string-statistics">[%s]</span>' % stringstatstext
    return filestats + wordstats + stringstats

  def getstatsheadings(self):
    """returns a dictionary of localised headings"""
    headings = {"name": self.localize("Name"),
                "translated": self.localize("Translated"),
                "translatedpercentage": self.localize("Translated percentage"),
                "translatedwords": self.localize("Translated words"),
                "fuzzy": self.localize("Fuzzy"),
                "fuzzypercentage": self.localize("Fuzzy percentage"),
                "fuzzywords": self.localize("Fuzzy words"),
                "untranslated": self.localize("Untranslated"),
                "untranslatedpercentage": self.localize("Untranslated percentage"),
                "untranslatedwords": self.localize("Untranslated words"),
                "total": self.localize("Total"),
                "totalwords": self.localize("Total words"),
                # l10n: noun. The graphical representation of translation status
                "progress": self.localize("Progress"),
                "summary": self.localize("Summary")}
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
                  "text": self.localize("Source Text"),
                  "value": self.argdict.get("source", 0),
                  "checked": self.argdict.get("source", 0) == "1" and "checked" or None},
                 {"name": "target",
                  "text": self.localize("Target Text"),
                  "value": self.argdict.get("target", 0),
                  "checked": self.argdict.get("target", 0) == "1" and "checked" or None},
                 {"name": "notes",
                  "text": self.localize("Comments"),
                  "value": self.argdict.get("notes", 0),
                  "checked": self.argdict.get("notes", 0) == "1" and "checked" or None},
                 {"name": "locations",
                  "text": self.localize("Locations"),
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


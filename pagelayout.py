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

from Pootle.storage_client import getstats as new_getstats
from Pootle.utils import getbrowseurl as new_getbrowseurl
from Pootle.utils import makelink as new_makelink
from Pootle.utils import makenavbarpath_dict as new_makenavbarpath_dict
from Pootle.utils import deprecated

def layout_banner(maxheight):
  """calculates dimensions, image name for banner"""
  logo_width, logo_height = min((98*maxheight/130, maxheight), (98, 130))
  banner_width, banner_height = min((290*maxheight/160, maxheight), (290, 160))
  if logo_width <= 61:
    logo_image = "pootle-medium.png"
  else:
    logo_image = "pootle.png"
  return {"logo_width": logo_width, "logo_height": logo_height,
    "banner_width": banner_width, "banner_height": banner_height, "logo_image": logo_image}

# replaced with gettext in Django
def localize_links(session):
  """Localize all the generic links"""
  links = {}
  links["home"] = session.localize("Home")
  links["projects"] = session.localize("All projects")
  links["languages"] = session.localize("All languages")
  links["account"] = session.localize("My account")
  links["admin"] = session.localize("Admin")
  links["doc"] = session.localize("Docs & help")
  links["logout"] = session.localize("Log out")
  links["login"] = session.localize("Log in")
  #l10n: Verb, as in "to register"
  links["register"] = session.localize("Register")
  links["activate"] = session.localize("Activate")
  return links

# this is replaced with request.LANGUAGE_BIDI in Django
def languagedir(language):
  """Returns whether the language is right to left"""
  for code in ["ar", "fa", "he", "ks", "ps", "ur", "yi"]:
    if language.startswith(code):
      return "rtl"
  return "ltr"

def weblanguage(language):
  """Reformats the language from locale style (pt_BR) to web style (pt-BR)"""
  return language.replace("_", "-")
    
# this is replaced with context_processors in Django
def completetemplatevars(templatevars, session, bannerheight=135):
  """fill out default values for template variables"""
  if not "instancetitle" in templatevars:
    templatevars["instancetitle"] = getattr(session.instance, "title", session.localize("Pootle Demo"))
  if not "session" in templatevars:
    templatevars["session"] = {"status": session.status, "isopen": session.isopen, "issiteadmin": session.issiteadmin()}
  banner_layout = layout_banner(bannerheight)
  banner_layout["logo_alttext"] = session.localize("Pootle Logo")
  banner_layout["banner_alttext"] = session.localize("WordForge Translation Project")
  templatevars.update(banner_layout)
  templatevars["aboutlink"] = session.localize("About this Pootle server")
  templatevars["uilanguage"] = weblanguage(session.language)
  templatevars["uidir"] = languagedir(session.language)
  templatevars["links"] = localize_links(session)
  if "search" not in templatevars:
    templatevars["search"] = None

class PootlePage:
  """the main page"""
  def __init__(self, templatename, templatevars, session, bannerheight=135):
    if not hasattr(session.instance, "baseurl"):
      session.instance.baseurl = "/"
    self.localize = session.localize
    self.session = session
    self.templatename = templatename
    self.templatevars = templatevars
    self.completevars(bannerheight)

  def completevars(self, bannerheight=135):
    """fill out default values for template variables"""
    if hasattr(self, "templatevars"):
      completetemplatevars(self.templatevars, self.session, bannerheight=bannerheight)

  # this is replaced by templatetag in Django
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

class PootleNavPage(PootlePage):
  # migration note: no variables referenced from self, just methods
  def makenavbarpath_dict(self, project=None, session=None, currentfolder=None, language=None, argdict={}):
    return new_makenavbarpath_dict(project, session, currentfolder, language, argdict)
  makenavbarpath_dict = deprecated(makenavbarpath_dict)

  def getbrowseurl(self, basename, **newargs):
    return new_getbrowseurl(self.argdict, basename, **newargs)
  getbrowseurl = deprecated(getbrowseurl)

  def makelink(self, link, **newargs):
    return new_makelink(self.argdict, link, **newargs)
  makelink = deprecated(makelink)

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
    total = projectstats.get("total", [])
    if "translatedwords" in projectstats:
      translatedwords = projectstats["translatedwords"]
    else:
      translatedwords = project.countwords(translated)
    if "totalwords" in projectstats:
      totalwords = projectstats["totalwords"]
    else:
      totalwords = project.countwords(total)
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
                "graph": self.localize("Graph")}
    return headings

  def getstats(self, project, projectstats, numfiles):
    """returns a list with the data items to fill a statistics table
    Remember to update getstatsheadings() above as needed"""
    # now in storage_client
    return new_getstats(project, projectstats, numfiles)


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

import re
from jToolkit import spellcheck
from Pootle import pagelayout
from Pootle import projects
from Pootle import pootlefile
from translate.storage import po
from translate.misc.multistring import multistring
import difflib
import operator
import urllib
import os

from django.contrib.auth.models import User
from Pootle import pan_app
from Pootle.pootle_app.models import get_profile
from Pootle.i18n.jtoolkit_i18n import localize, tr_lang

xml_re = re.compile("&lt;.*?&gt;")

def oddoreven(polarity):
  if polarity % 2 == 0:
    return "even"
  elif polarity % 2 == 1:
    return "odd"

class TranslatePage(pagelayout.PootleNavPage):
  """the page which lets people edit translations"""
  def __init__(self, project, request, argdict, dirfilter=None):
    self.argdict = argdict
    self.dirfilter = dirfilter
    self.project = project
    self.altproject = None
    # do we have enabled alternative source language?
    self.enablealtsrc = getattr(pan_app.prefs, "enablealtsrc", "False")
    if self.enablealtsrc == 'True':
      # try to get the project if the user has chosen an alternate source language
      altsrc = request.getaltsrclanguage()
      if altsrc != '':
        try:
          self.altproject = self.project.potree.getproject(altsrc, self.project.projectcode)
        except IndexError:
          pass
    self.matchnames = self.getmatchnames(self.project.checker)
    self.searchtext = self.argdict.get("searchtext", "")
    # TODO: fix this in jToolkit
    if isinstance(self.searchtext, str):
      self.searchtext = self.searchtext.decode("utf8")
    self.showassigns = self.argdict.get("showassigns", 0)
    if isinstance(self.showassigns, (str, unicode)) and self.showassigns.isdigit():
      self.showassigns = int(self.showassigns)
    self.request = request
    self.rights = self.project.getrights(self.request)
    if "view" not in self.rights:
      raise projects.Rights404Error(None)
    self.lastitem = None
    self.pofilename = self.argdict.pop("pofilename", None)
    if self.pofilename == "":
      self.pofilename = None
    if self.pofilename is None and self.dirfilter is not None and \
            (self.dirfilter.endswith(".po") or self.dirfilter.endswith(".xlf")):
      self.pofilename = self.dirfilter
    self.receivetranslations()
    # TODO: clean up modes to be one variable
    self.viewmode = self.argdict.get("view", 0) and "view" in self.rights
    self.reviewmode = self.argdict.get("review", 0)
    self.translatemode = (self.argdict.get("translate", 0) or self.argdict.get("searchtext", 0)) and ("translate" in self.rights or "suggest" in self.rights)
    notice = {}
    try:
      self.finditem()
    except StopIteration, stoppedby:
      notice = self.getfinishedtext(stoppedby)
      self.item = None
    items = self.maketable()
    # self.pofilename can change in search...
    givenpofilename = self.pofilename
    formaction = self.makelink("")
    mainstats = ""
    pagelinks = None
    if self.viewmode:
      rows = self.getdisplayrows("view")
      icon="file"
    else:
      rows = self.getdisplayrows("translate")
      icon="edit"
    if self.pofilename is not None:
      postats = self.project.getpototals(self.pofilename)
      untranslated, fuzzy = postats["total"] - postats["translated"], postats["fuzzy"]
      translated, total = postats["translated"], postats["total"]
      mainstats = localize("%d/%d translated\n(%d untranslated, %d fuzzy)", translated, total, untranslated, fuzzy)
      pagelinks = self.getpagelinks("?translate=1&view=1", rows)
    navbarpath_dict = self.makenavbarpath_dict(self.project, self.request, self.pofilename, dirfilter=self.dirfilter or "")
    # templatising
    templatename = "translatepage"
    instancetitle = getattr(pan_app.prefs, "title", localize("Pootle Demo"))
    # l10n: first parameter: name of the installation (like "Pootle")
    # l10n: second parameter: project name
    # l10n: third parameter: target language
    # l10n: fourth parameter: file name
    pagetitle = localize("%s: translating %s into %s: %s", instancetitle, self.project.projectname, self.project.languagename, self.pofilename)
    language = {"code": pagelayout.weblanguage(self.project.languagecode), "name": self.project.languagename, "dir": pagelayout.languagedir(self.project.languagecode)}
    sessionvars = {"status": get_profile(request.user).status, "isopen": not request.user.is_anonymous, "issiteadmin": request.user.is_superuser}
    stats = {"summary": mainstats, "checks": [], "tracks": [], "assigns": []}

    templatevars = {"pagetitle": pagetitle,
        "project": {"code": self.project.projectcode, "name": self.project.projectname},
        "language": language,
        "pofilename": self.pofilename,
        # navigation bar
        "navitems": [{"icon": icon, "path": navbarpath_dict, "actions": {}, "stats": stats}],
        "pagelinks": pagelinks,
        # translation form
        "actionurl": formaction,
        "notice": notice,
        # l10n: Heading above the table column with the source language
        "original_title": localize("Original"),
        # l10n: Heading above the table column with the target language
        "translation_title": localize("Translation"),
        "items": items,
        "reviewmode": self.reviewmode,
        "accept_title": localize("Accept suggestion"),
        "reject_title": localize("Reject suggestion"),
        "fuzzytext": localize("Fuzzy"),
        # l10n: Ajax link for suggestions.  %s is the number of suggestions
        "viewsuggtext": localize("View Suggestions (%s)"),
        # l10n: Heading above the textarea for translator comments.
        "translator_comments_title": localize("Translator comments"),
        # l10n: Heading above the comments extracted from the programing source code
        "developer_comments_title": localize("Developer comments"),
        # l10n: This heading refers to related translations and terminology
        "related_title": localize("Related"),
        # optional sections, will appear if these values are replaced
        "assign": None,
        # l10n: text next to search field
        "search": {"title": localize("Search"),
                   "advanced_title": localize("Advanced Search"),
                   "fields": self.getsearchfields()},
        # hidden widgets
        "searchtext": self.searchtext,
        "pofilename": givenpofilename,
        # general vars
        "session": sessionvars,
        "instancetitle": instancetitle,
        "rights": self.rights,
        # l10n: Text displayed when an AJAX petition is being made
        "ajax_status_text": localize("Working..."),
        # l10n: Text displayed in an alert box when an AJAX petition has failed
        "ajax_error": localize("Error: Something went wrong."),
        # l10n: Button label
        "accept_button": localize("Accept"),
        # l10n: Button label
        "reject_button": localize("Reject")
        }

    if self.extra_class:
      templatevars["search"]["extra_class"] = "nodefaultsearch"

    if self.showassigns and "assign" in self.rights:
      templatevars["assign"] = self.getassignbox()
    pagelayout.PootleNavPage.__init__(self, templatename, templatevars, request, bannerheight=81)
    self.addfilelinks()

  def getfinishedtext(self, stoppedby):
    """gets notice to display when the translation is finished"""
    # l10n: "batch" refers to the set of translations that were reviewed
    title = localize("End of batch")
    finishedlink = "index.html?" + "&".join(["%s=%s" % (arg, value) for arg, value in self.argdict.iteritems() if arg.startswith("show") or arg == "editing"])
    returnlink = localize("Click here to return to the index")
    stoppedbytext = stoppedby.args[0]
    return {"title": title, "stoppedby": stoppedbytext, "finishedlink": finishedlink, "returnlink": returnlink}

  def getpagelinks(self, baselink, pagesize):
    """gets links to other pages of items, based on the given baselink"""
    baselink += "&pofilename=%s" % self.pofilename
    pagelinks = []
    pofilelen = self.project.getpofilelen(self.pofilename)
    if pofilelen <= pagesize or self.firstitem is None:
      return pagelinks
    lastitem = min(pofilelen-1, self.firstitem + pagesize - 1)
    if pofilelen > pagesize and not self.firstitem == 0:
      # l10n: noun (the start)
      pagelinks.append({"href": baselink + "&item=0", "text": localize("Start")})
    else:
      # l10n: noun (the start)
      pagelinks.append({"text": localize("Start")})
    if self.firstitem > 0:
      linkitem = max(self.firstitem - pagesize, 0)
      # l10n: the parameter refers to the number of messages
      pagelinks.append({"href": baselink + "&item=%d" % linkitem, "text": localize("Previous %d", (self.firstitem - linkitem))})
    else:
      # l10n: the parameter refers to the number of messages
      pagelinks.append({"text": localize("Previous %d", pagesize)})
      # l10n: the third parameter refers to the total number of messages in the file
    pagelinks.append({"text": localize("Items %d to %d of %d", self.firstitem+1, lastitem+1, pofilelen)})
    if self.firstitem + len(self.translations) < self.project.getpofilelen(self.pofilename):
      linkitem = self.firstitem + pagesize
      itemcount = min(pofilelen - linkitem, pagesize)
      # l10n: the parameter refers to the number of messages
      pagelinks.append({"href": baselink + "&item=%d" % linkitem, "text": localize("Next %d", itemcount)})
    else:
      # l10n: the parameter refers to the number of messages
      pagelinks.append({"text": localize("Next %d", pagesize)})
    if pofilelen > pagesize and (self.item + pagesize) < pofilelen:
      # l10n: noun (the end)
      pagelinks.append({"href": baselink + "&item=%d" % max(pofilelen - pagesize, 0), "text": localize("End")})
    else:
      # l10n: noun (the end)
      pagelinks.append({"text": localize("End")})
    for n, pagelink in enumerate(pagelinks):
      if n < len(pagelinks)-1:
        pagelink["sep"] = " | "
      else:
        pagelink["sep"] = ""
    return pagelinks

  def addfilelinks(self):
    """adds a section on the current file, including any checks happening"""
    if self.showassigns and "assign" in self.rights:
      self.templatevars["assigns"] = self.getassignbox()
    if self.pofilename is not None:
      if self.matchnames:
        checknames = \
        ["<a href='http://translate.sourceforge.net/wiki/toolkit/pofilter_tests#%(checkname)s' \
        title='%(checkname)s' target='_blank'>%(checkname)s</a>" % \
        {"checkname": matchname.replace("check-", "", 1)} for matchname in self.matchnames]
        # TODO: put the following parameter in quotes, since it will be foreign in all target languages
        # l10n: the parameter is the name of one of the quality checks, like "fuzzy"
        self.templatevars["checking_text"] = localize("checking %s", ", ".join(checknames))

  def getassignbox(self):
    """gets strings if the user can assign strings"""
    users = User.objects.order_by('username')
    return {
      "title": localize("Assign Strings"),
      "user_title": localize("Assign to User"),
      "action_title": localize("Assign Action"),
      "submit_text": localize("Assign Strings"),
      "users": users,
    }

  def receivetranslations(self):
    """receive any translations submitted by the user"""
    if self.pofilename is None:
      return
    backs = []
    skips = []
    submitsuggests = []
    submits = []
    accepts = []
    rejects = []
    translations = {}
    suggestions = {}
    comments = {}
    fuzzies = {}
    keymatcher = re.compile("(\D+)([0-9.]+)")
    def parsekey(key):
      match = keymatcher.match(key)
      if match:
        keytype, itemcode = match.groups()
        return keytype, itemcode
      return None, None
    def pointsplit(item):
      dotcount = item.count(".")
      if dotcount == 2:
        item, pointitem, subpointitem = item.split(".", 2)
        return int(item), int(pointitem), int(subpointitem)
      elif dotcount == 1:
        item, pointitem = item.split(".", 1)
        return int(item), int(pointitem), None
      else:
        return int(item), None, None
    delkeys = []
    for key, value in self.argdict.iteritems():
      keytype, item = parsekey(key)
      if keytype is None:
        continue
      item, pointitem, subpointitem = pointsplit(item)
      if keytype == "skip":
        skips.append(item)
      elif keytype == "back":
        backs.append(item)
      elif keytype == "submitsuggest":
        submitsuggests.append(item)
      elif keytype == "submit":
        submits.append(item)
      elif keytype == "accept":
        accepts.append((item, pointitem))
      elif keytype == "reject":
        rejects.append((item, pointitem))
      elif keytype == "translator_comments":
        # We need to remove carriage returns from the input.
        value = value.replace("\r", "")
        comments[item] = value
      elif keytype == "fuzzy":
        fuzzies[item] = value
      elif keytype == "trans":
        value = self.unescapesubmition(value)
        if pointitem is not None:
          translations.setdefault(item, {})[pointitem] = value
        else:
          translations[item] = value
      elif keytype == "suggest":
        suggestions.setdefault((item, pointitem), {})[subpointitem] = value
      elif keytype == "orig-pure":
        # this is just to remove the hidden fields from the argdict
        pass
      else:
        continue
      delkeys.append(key)


    for key in delkeys:
      del self.argdict[key]
    for item in skips:
      self.lastitem = item
    for item in backs:
      self.lastitem = item - 2
    for item in submitsuggests:
      if item in skips or item not in translations:
        continue
      value = translations[item]
      self.project.suggesttranslation(self.pofilename, item, value, self.request)
      self.lastitem = item

    for item in submits:
      if item in skips or item not in translations:
        continue

      newvalues = {}
      newvalues["target"] = translations[item]
      if isinstance(newvalues["target"], dict) and len(newvalues["target"]) == 1 and 0 in newvalues["target"]:
        newvalues["target"] = newvalues["target"][0]

      newvalues["fuzzy"] = False
      if (fuzzies.get(item) == u'on'):
        newvalues["fuzzy"] = True

      translator_comments = comments.get(item)
      if translator_comments:
        newvalues["translator_comments"] = translator_comments

      self.project.updatetranslation(self.pofilename, item, newvalues, self.request)

      self.lastitem = item

    # Make sure we have rejects list properly sorted
    rejects.sort(key=operator.itemgetter(1))
    # It's necessary to loop the list reversed in order to selectively remove items
    for item, suggid in reversed(rejects):
      value = suggestions[item, suggid]
      if isinstance(value, dict) and len(value) == 1 and 0 in value:
        value = value[0]
      self.project.rejectsuggestion(self.pofilename, item, suggid, value, self.request)
      self.lastitem = item
    for item, suggid in accepts:
      if (item, suggid) in rejects or (item, suggid) not in suggestions:
        continue
      value = suggestions[item, suggid]
      if isinstance(value, dict) and len(value) == 1 and 0 in value:
        value = value[0]
      self.project.acceptsuggestion(self.pofilename, item, suggid, value, self.request)
      self.lastitem = item

  def getmatchnames(self, checker):
    """returns any checker filters the user has asked to match..."""
    matchnames = []
    for checkname in self.argdict:
      if checkname in ["fuzzy", "untranslated", "translated"]:
        matchnames.append(checkname)
      elif checkname in checker.getfilters():
        matchnames.append("check-" + checkname)
    matchnames.sort()
    return matchnames

  def getusernode(self):
    """gets the user's prefs node"""
    if not self.request.user.is_anonymous:
      return User.objects.filter(username=self.request.username)[0]
    else:
      return None

  def finditem(self):
    """finds the focussed item for this page, searching as neccessary"""
    item = self.argdict.pop("item", None)
    if item is None:
      try:
        # Retrieve the search fields we want to search for
        fields = [f["name"] for f in self.getsearchfields() if f["value"] == "1"]
        search = pootlefile.Search(dirfilter=self.dirfilter, matchnames=self.matchnames, searchtext=self.searchtext, searchfields=fields)
        # TODO: find a nicer way to let people search stuff assigned to them (does it by default now)
        # search.assignedto = self.argdict.get("assignedto", self.request.username)
        search.assignedto = self.argdict.get("assignedto", None)
        search.assignedaction = self.argdict.get("assignedaction", None)
        self.pofilename, self.item = self.project.searchpoitems(self.pofilename, self.lastitem, search).next()
      except StopIteration:
        if self.lastitem is None:
          raise StopIteration(localize("There are no items matching that search ('%s')", self.searchtext))
        else:
          raise StopIteration(localize("You have finished going through the items you selected"))
    else:
      if not item.isdigit():
        raise ValueError("Invalid item given")
      self.item = int(item)
      if self.pofilename is None:
        raise ValueError("Received item argument but no pofilename argument")
    self.project.track(self.pofilename, self.item, "being edited by %s" % self.request.user.username)

  def getdisplayrows(self, mode):
    """get the number of rows to display for the given mode"""
    if mode == "view":
      prefsfield = "viewrows"
      default = 10
      maximum = 100
    elif mode == "translate":
      prefsfield = "translaterows"
      default = 7
      maximum = 20
    else:
      raise ValueError("getdisplayrows has no mode '%s'" % mode)
    usernode = self.getusernode()
    rowsdesired = getattr(usernode, prefsfield, default)
    if isinstance(rowsdesired, basestring):
      if rowsdesired == "":
        rowsdesired = default
      else:
        rowsdesired = int(rowsdesired)
    rowsdesired = min(rowsdesired, maximum)
    return rowsdesired

  def gettranslations(self):
    """gets the list of translations desired for the view, and sets editable and firstitem parameters"""
    if self.item is None:
      self.editable = []
      self.firstitem = self.item
      return []
    elif self.viewmode:
      self.editable = []
      self.firstitem = self.item
      rows = self.getdisplayrows("view")
      return self.project.getitems(self.pofilename, self.item, self.item+rows)
    else:
      self.editable = [self.item]
      rows = self.getdisplayrows("translate")
      before = 0; 
      fromitem = self.item - before
      self.firstitem = max(self.item - before, 0)
      toitem = self.firstitem + rows
      return self.project.getitems(self.pofilename, fromitem, toitem)

  def maketable(self):
    self.translations = self.gettranslations()
    items = []
    suggestions = {}
    if (self.reviewmode or self.translatemode) and self.item is not None:
      suggestions = {self.item: self.project.getsuggestions(self.pofilename, self.item)}
    for row, unit in enumerate(self.translations):
      tmsuggestions = []
      if isinstance(unit.source, multistring):
        orig = unit.source.strings
      else:
        orig = [unit.source]
      if isinstance(unit.target, multistring):
        trans = unit.target.strings
      else:
        trans = [unit.target]
      nplurals, plurals = self.project.getpofile(self.pofilename).getheaderplural()
      try:
        if len(orig) > 1:
          if not (nplurals and nplurals.isdigit()):
            # The file doesn't have plural information declared. Let's get it from
            # the language
            nplurals = getattr(self.project.potree.languages[self.project.languagecode], "nplurals", "")
          nplurals = int(nplurals)
          if len(trans) != nplurals:
            # Chop if in case it is too long
            trans = trans[:nplurals]
            trans.extend([u""]* (nplurals-len(trans)))
      except Exception:
        # Something went wrong, lets just give nothing
        trans = []
      item = self.firstitem + row
      origdict = self.getorigdict(item, orig, item in self.editable)
      transmerge = {}
      suggestions[item] = self.project.getsuggestions(self.pofilename, item)

      message_context = ""
      if item in self.editable:
        translator_comments = unit.getnotes(origin="translator")
        developer_comments = self.escapetext(unit.getnotes(origin="developer"), stripescapes=True)
        locations = " ".join(unit.getlocations())
        if isinstance(unit, po.pounit):
          message_context = "".join(unit.getcontext())
        tmsuggestions = self.project.gettmsuggestions(self.pofilename, self.item)
        tmsuggestions.extend(self.project.getterminology(self.request, self.pofilename, self.item))

        transmerge = self.gettransedit(item, trans)
      else:
        translator_comments = unit.getnotes(origin="translator")
        developer_comments = unit.getnotes(origin="developer")
        locations = ""
        transmerge = self.gettransview(item, trans)

      itemsuggestions = []
      for suggestion in suggestions[item]:
        if suggestion.hasplural():
          itemsuggestions.append(suggestion.target.strings)
        else:
          itemsuggestions.append([suggestion.target])
      transreview = self.gettransreview(item, trans, itemsuggestions)
      if 'forms' in transmerge.keys():
        for fnum in range(len(transmerge['forms'])):
          transreview['forms'][fnum].update(transmerge['forms'][fnum])
      elif 'text' in transmerge.keys():
        transreview['forms'][0]['text'] = transmerge['text']
 
      transmerge.update(transreview)

      transdict = {"itemid": "trans%d" % item,
                   "focus_class": origdict["focus_class"],
                   "isplural": len(trans) > 1,
                  }
      transdict.update(transmerge)
      polarity = oddoreven(item)
      if item in self.editable:
        focus_class = "translate-focus"
      else:
        focus_class = ""

      state_class = ""
      fuzzy = None
      if unit.isfuzzy():
        state_class += "translate-translation-fuzzy"
        fuzzy = "checked"

      hassuggestion = len(transdict.get("suggestions", {})) > 0

      itemdict = {
                 "itemid": item,
                 "orig": origdict,
                 "trans": transdict,
                 "polarity": polarity,
                 "focus_class": focus_class,
                 "editable": item in self.editable,
                 "state_class": state_class,
                 "fuzzy": fuzzy,
                 "translator_comments": translator_comments,
                 "developer_comments": developer_comments,
                 "locations": locations,
                 "message_context": message_context,
                 "tm": tmsuggestions,
                 "hassuggestion": hassuggestion
                 }

      altsrcdict = {"available": False}
      # do we have enabled alternative source language?
      if self.enablealtsrc == 'True':
        # get alternate source project information in a dictionary
        if item in self.editable:
          altsrcdict = self.getaltsrcdict(origdict)
      itemdict["altsrc"] = altsrcdict

      items.append(itemdict)
    return items

  def fancyspaces(self, string):
    """Returns the fancy spaces that are easily visible."""
    spaces = string.group()
    while spaces[0] in "\t\n\r":
      spaces = spaces[1:]
    return '<span class="translation-space"> </span>\n' * len(spaces)

  def escapetext(self, text, fancyspaces=True, stripescapes=False):
    """Replace special characters &, <, >, add and handle escapes if asked."""
    text = text.replace("&", "&amp;") # Must be done first!
    text = text.replace("<", "&lt;").replace(">", "&gt;")

    if stripescapes:
      text = text.replace("\n", '<br />')
      text = text.replace("\r", '<br />')
    else:
      fancyescape = lambda escape: \
          '<span class="translation-highlight-escape">%s</span>' % escape
      fancy_xml = lambda escape: \
            '<span class="translation-highlight-html">%s</span>' % escape.group()
      text = xml_re.sub(fancy_xml, text)

      text = text.replace("\r\n", fancyescape('\\r\\n') + '<br />')
      text = text.replace("\n", fancyescape('\\n') + '<br />')
      text = text.replace("\r", fancyescape('\\r') + '<br />')
      text = text.replace("\t", fancyescape('\\t'))
    text = text.replace("<br />", '<br />\n')
    # we don't need it at the end of the string
    if text.endswith("<br />\n"):
      text = text[:-len("<br />\n")]

    if fancyspaces:
      text = self.addfancyspaces(text)
    return text

  def addfancyspaces(self, text):
    """Insert fancy spaces"""
    #More than two consecutive:
    text = re.sub("[ ]{2,}", self.fancyspaces, text)
    #At start of string
    text = re.sub("^[ ]+", self.fancyspaces, text)
    #After newline
    text = re.sub("\\n([ ]+)", self.fancyspaces, text)
    #At end of string
    text = re.sub("[ ]+$", self.fancyspaces, text)
    return text

  def escapefortextarea(self, text):
    text = text.replace("&", "&amp;") # Must be done first!
    text = text.replace("<", "&lt;").replace(">", "&gt;")
    text = text.replace("\r\n", '\\r\\n')
    text = text.replace("\n", '\\n')
    text = text.replace("\\n", '\\n\n')
    text = text.replace("\t", '\\t')
    return text

  def unescapesubmition(self, text):
    text = text.replace("\t", "")
    text = text.replace("\n", "")
    text = text.replace("\r", "")
    text = text.replace("\\t", "\t")
    text = text.replace("\\n", "\n")
    text = text.replace("\\r", "\r")
    return text

  def getorigdict(self, item, orig, editable):
    if editable:
      focus_class = "translate-original-focus"
    else:
      focus_class = ""
    purefields = []
    for pluralid, pluraltext in enumerate(orig):
      pureid = "orig-pure%d.%d" % (item, pluralid)
      purefields.append({"pureid": pureid, "name": pureid, "value": pluraltext})
    origdict = {
           "focus_class": focus_class,
           "itemid": "orig%d" % item,
           "pure": purefields,
           "isplural": len(orig) > 1 or None,
           "singular_title": localize("Singular"),
           "plural_title": localize("Plural"),
           }
    if len(orig) > 1:
      origdict["singular_text"] = self.escapetext(orig[0])
      origdict["plural_text"] = self.escapetext(orig[1])
    else:
      origdict["text"] = self.escapetext(orig[0])
    return origdict

  def geteditlink(self, item):
    """gets a link to edit the given item, if the user has permission"""
    if "translate" in self.rights or "suggest" in self.rights:
      translateurl = "?translate=1&item=%d&pofilename=%s" % (item, urllib.quote(self.pofilename, '/'))
      # l10n: verb
      return {"href": translateurl, "text": localize("Edit"), "linkid": "editlink%d" % item}
    else:
      return {}

  def gettransbuttons(self, item, desiredbuttons):
    """gets buttons for actions on translation"""
    if "suggest" in desiredbuttons and "suggest" not in self.rights:
      desiredbuttons.remove("suggest")
    if "translate" in desiredbuttons and "translate" not in self.rights:
      desiredbuttons.remove("translate")
    specialchars = getattr(getattr(self.project.potree.languages, self.project.languagecode, None), "specialchars", "")
    if isinstance(specialchars, str):
      specialchars = specialchars.decode("utf-8")
    return {"desired": desiredbuttons,
            "item": item,
            # l10n: verb
            "copy_text": localize("Copy"),
            "skip": localize("Skip"),
            # l10n: verb
            "back": localize("Back"),
            "suggest": localize("Suggest"),
            "submit": localize("Submit"),
            "specialchars": specialchars,
            # l10n: action that increases the height of the textarea
            "grow": localize("Grow"),
            # l10n: action that decreases the height of the textarea
            "shrink": localize("Shrink"),
            # l10n: action that increases the width of the textarea
           }

  def gettransedit(self, item, trans):
    """returns a widget for editing the given item and translation"""
    transdict = {
                "rows": 5,
                "cols": 40,
                }
    if "translate" in self.rights or "suggest" in self.rights:
      usernode = self.getusernode()
      transdict = {
                  "rows": getattr(usernode, "inputheight", 5),
                  "cols": getattr(usernode, "inputwidth", 40),
                  }
      focusbox = ""
      spellargs = {"standby_url": "spellingstandby.html", "js_url": "/js/spellui.js", "target_url": "spellcheck.html"}
      if len(trans) > 1:
        buttons = self.gettransbuttons(item, ["back", "skip", "copy", "suggest", "translate"])
        forms = []
        for pluralitem, pluraltext in enumerate(trans):
          pluralform = localize("Plural Form %d", pluralitem)
          pluraltext = self.escapefortextarea(pluraltext)
          textid = "trans%d.%d" % (item, pluralitem)
          forms.append({"title": pluralform, "name": textid, "text": pluraltext, "n": pluralitem})
          if not focusbox:
            focusbox = textid
        transdict["forms"] = forms
      elif trans:
        buttons = self.gettransbuttons(item, ["back", "skip", "copy", "suggest", "translate"])
        transdict["text"] = self.escapefortextarea(trans[0])
        textid = "trans%d" % item
        focusbox = textid
      else:
        # Perhaps there is no plural information available
        buttons = self.gettransbuttons(item, ["back", "skip"])
        # l10n: This is an error message that will display if the relevant problem occurs
        transdict["text"] = self.escapefortextarea(localize("Translation not possible because plural information for your language is not available. Please contact the site administrator."))
        textid = "trans%d" % item
        focusbox = textid

      transdict["can_spell"] = spellcheck.can_check_lang(self.project.languagecode)
      transdict["spell_args"] = spellargs
      transdict["buttons"] = buttons
      transdict["focusbox"] = focusbox
    else:
      # TODO: work out how to handle this (move it up?)
      transdict.update(self.gettransview(item, trans, textarea=True))
      buttons = self.gettransbuttons(item, ["back", "skip"])
    transdict["buttons"] = buttons
    return transdict

  def highlightdiffs(self, text, diffs, issrc=True):
    """highlights the differences in diffs in the text.
    diffs should be list of diff opcodes
    issrc specifies whether to use the src or destination positions in reconstructing the text
    this escapes the text on the fly to prevent confusion in escaping the highlighting"""
    if issrc:
      diffstart = [(i1, 'start', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
      diffstop = [(i2, 'stop', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
    else:
      diffstart = [(j1, 'start', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
      diffstop = [(j2, 'stop', tag) for (tag, i1, i2, j1, j2) in diffs if tag != 'equal']
    diffswitches = diffstart + diffstop
    diffswitches.sort()
    textdiff = ""
    textnest = 0
    textpos = 0
    spanempty = False
    for i, switch, tag in diffswitches:
      textsection = self.escapetext(text[textpos:i])
      textdiff += textsection
      if textsection:
        spanempty = False
      if switch == 'start':
        textnest += 1
      elif switch == 'stop':
        textnest -= 1
      if switch == 'start' and textnest == 1:
        # start of a textition
        textdiff += "<span class='translate-diff-%s'>" % tag
        spanempty = True
      elif switch == 'stop' and textnest == 0:
        # start of an equals block
        if spanempty:
          # FIXME: work out why kid swallows empty spans, and browsers display them horribly, then remove this
          textdiff += "()"
        textdiff += "</span>"
      textpos = i
    textdiff += self.escapetext(text[textpos:])
    return textdiff

  def getdiffcodes(self, cmp1, cmp2):
    """compares the two strings and returns opcodes"""
    return difflib.SequenceMatcher(None, cmp1, cmp2).get_opcodes()

  def gettransreview(self, item, trans, suggestions):
    """returns a widget for reviewing the given item's suggestions"""
    hasplurals = len(trans) > 1
    diffcodes = {}
    for pluralitem, pluraltrans in enumerate(trans):
      if isinstance(pluraltrans, str):
        trans[pluralitem] = pluraltrans.decode("utf-8")
    for suggestion in suggestions:
      for pluralitem, pluralsugg in enumerate(suggestion):
        if isinstance(pluralsugg, str):
          suggestion[pluralitem] = pluralsugg.decode("utf-8")
    forms = []
    for pluralitem, pluraltrans in enumerate(trans):
      pluraldiffcodes = [self.getdiffcodes(pluraltrans, suggestion[pluralitem]) for suggestion in suggestions]
      diffcodes[pluralitem] = pluraldiffcodes
      combineddiffs = reduce(list.__add__, pluraldiffcodes, [])
      transdiff = self.highlightdiffs(pluraltrans, combineddiffs, issrc=True)
      form = {"n": pluralitem, "diff": transdiff, "title": None}
      if hasplurals:
        pluralform = localize("Plural Form %d", pluralitem)
        form["title"] = pluralform
      forms.append(form)
    transdict = {
                "current_title": localize("Current Translation:"),
                "editlink": self.geteditlink(item),
                "forms": forms,
                "isplural": hasplurals or None,
                "itemid": "trans%d" % item,
                }
    suggitems = []
    for suggid, msgstr in enumerate(suggestions):
      suggestedby = self.project.getsuggester(self.pofilename, item, suggid)
      if len(suggestions) > 1:
        if suggestedby:
          # l10n: First parameter: number
          # l10n: Second parameter: name of translator
          suggtitle = localize("Suggestion %d by %s:", suggid+1, suggestedby)
        else:
          suggtitle = localize("Suggestion %d:", suggid+1)
      else:
        if suggestedby:
          # l10n: parameter: name of translator
          suggtitle = localize("Suggestion by %s:", suggestedby)
        else:
          suggtitle = localize("Suggestion:")
      forms = []
      for pluralitem, pluraltrans in enumerate(trans):
        pluralsuggestion = msgstr[pluralitem]
        suggdiffcodes = diffcodes[pluralitem][suggid]
        suggdiff = self.highlightdiffs(pluralsuggestion, suggdiffcodes, issrc=False)
        if isinstance(pluralsuggestion, str):
          pluralsuggestion = pluralsuggestion.decode("utf8")
        form = {"diff": suggdiff}
        form["suggid"] = "suggest%d.%d.%d" % (item, suggid, pluralitem)
        form["value"] = pluralsuggestion
        if hasplurals:
          form["title"] = localize("Plural Form %d", pluralitem)
        forms.append(form)
      suggdict = {"title": suggtitle,
                  "author": suggestedby,
                  "forms": forms,
                  "suggid": "%d.%d" % (item, suggid),
                  "canreview": "review" in self.rights,
                  "back": None,
                  "skip": None,
                 }
      suggitems.append(suggdict)
    # l10n: verb
    backbutton = {"item": item, "text": localize("Back")}
    skipbutton = {"item": item, "text": localize("Skip")}
    if suggitems:
      suggitems[-1]["back"] = backbutton
      suggitems[-1]["skip"] = skipbutton
    else:
      transdict["back"] = backbutton
      transdict["skip"] = skipbutton
    transdict["suggestions"] = suggitems
    return transdict

  def gettransview(self, item, trans, textarea=False):
    """returns a widget for viewing the given item's translation"""
    if textarea:
      escapefunction = self.escapefortextarea
    else:
      escapefunction = self.escapetext
    editlink = self.geteditlink(item)
    transdict = {"editlink": editlink}

    cansugg = "suggest" in self.rights 
    cantrans = "translate" in self.rights
    ables = ""
    if cansugg: 
      ables = "suggestable "+ables
    if cantrans: 
      ables = "submitable "+ables

    if len(trans) > 1:
      forms = []
      for pluralitem, pluraltext in enumerate(trans):
        form = {"title": localize("Plural Form %d", pluralitem), "n": pluralitem, "text": escapefunction(pluraltext)}
        editclass = ""
        if cantrans or cansugg: 
          editclass = ables+"edittrans"+str(item)+"p"+str(pluralitem)
        form["editclass"] = editclass

        forms.append(form)
      transdict["forms"] = forms
    elif trans:
      transdict["text"] = escapefunction(trans[0])
      editclass = ""
      if cantrans or cansugg: 
        editclass = ables+"edittrans"+str(item)
      transdict["editclass"] = editclass

    else:
      # Error, problem with plurals perhaps?
      transdict["text"] = ""
    return transdict

  def getaltsrcdict(self, origdict):
    # TODO: handle plurals !!
    altsrcdict = {"available": False}
    if self.altproject is not None:
      altsrcdict["languagecode"] = pagelayout.weblanguage(self.altproject.languagecode)
      altsrcdict["languagename"] = self.altproject.potree.getlanguagename(self.altproject.languagecode)
      altsrcdict["dir"] = pagelayout.languagedir(altsrcdict["languagecode"])
      altsrcdict["title"] = tr_lang(altsrcdict["languagename"])
      if not origdict["isplural"]:
        orig = origdict["pure"][0]["value"]
        altsrctext = self.altproject.ugettext(orig)
        if altsrctext != orig and not self.reviewmode:
          altsrcdict["text"] = self.escapetext(altsrctext)
          altsrcdict["available"] = True
    return altsrcdict


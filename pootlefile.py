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

"""manages po files and their associated files"""

from translate.storage import po
from translate.misc import quote
from translate.misc.multistring import multistring
from translate.filters import checks
from Pootle import __version__
from jToolkit import timecache
import time
import os

def getmodtime(filename, default=None):
  """gets the modificationtime of the given file"""
  if os.path.exists(filename):
    return os.stat(filename)[os.path.stat.ST_MTIME]
  else:
    return default

def wordcount(unquotedstr):
  """returns the number of words in an unquoted str"""
  return len(unquotedstr.split())

class pootleelement(po.pounit, object):
  """a pounit with helpful methods for pootle"""

  def classify(self, checker):
    """returns all classify keys that this element should match, using the checker"""
    classes = ["total"]
    if self.isfuzzy():
      classes.append("fuzzy")
    if self.isblankmsgstr():
      classes.append("blank")
    if not ("fuzzy" in classes or "blank" in classes):
      classes.append("translated")
    # TODO: we don't handle checking plurals at all yet, as this is tricky...
    source = self.source
    target = self.target
    if isinstance(source, str) and isinstance(target, unicode):
      source = source.decode(getattr(self, "encoding", "utf-8"))
    filterresult = checker.run_filters(self, source, target)
    for filtername, filtermessage in filterresult:
      classes.append("check-" + filtername)
    return classes

class pootlefile(po.pofile):
  """this represents a pootle-managed .po file and its associated files"""
  x_generator = "Pootle %s" % __version__.ver
  def __init__(self, project=None, pofilename=None, stats=True):
    po.pofile.__init__(self, unitclass=pootleelement)
    self.pofilename = pofilename
    if project is None:
      from Pootle import projects
      self.project = projects.DummyProject(None)
      #self.checker = None
      self.checker = self.project.checker
      self.filename = self.pofilename
    else:
      self.project = project
      self.checker = self.project.checker
      self.filename = os.path.join(self.project.podir, self.pofilename)
    self.statsfilename = self.filename + os.extsep + "stats"
    self.pendingfilename = self.filename + os.extsep + "pending"
    self.tmfilename = self.filename + os.extsep + "tm"
    self.assignsfilename = self.filename + os.extsep + "assigns"
    self.pendingfile = None
    # we delay parsing until it is required
    self.pomtime = None
    self.classify = {}
    self.msgidwordcounts = []
    self.msgstrwordcounts = []
    if stats:
      self.getstats()
    self.getassigns()
    self.tracker = timecache.timecache(20*60)

  def track(self, item, message):
    """sets the tracker message for the given item"""
    self.tracker[item] = message

  def readpofile(self):
    """reads and parses the main po file"""
    # make sure encoding is reset so it is read from the file
    self.encoding = None
    self.units = []
    pomtime = getmodtime(self.filename)
    self.parse(open(self.filename, 'r'))
    # we ignore all the headers by using this filtered set
    self.transelements = [poel for poel in self.units if not (poel.isheader() or poel.isblank())]
    self.classifyelements()
    self.pomtime = pomtime

  def savepofile(self):
    """saves changes to the main file to disk..."""
    output = str(self)
    open(self.filename, "w").write(output)
    # don't need to reread what we saved
    self.pomtime = getmodtime(self.filename)

  def pofreshen(self):
    """makes sure we have a freshly parsed pofile"""
    if not os.path.exists(self.filename):
      # the file has been removed, update the project index (and fail below)
      self.project.scanpofiles()
    if self.pomtime != getmodtime(self.filename):
      self.readpofile()

  def getoutput(self):
    """returns pofile output"""
    self.pofreshen()
    return super(pootlefile, self).getoutput()

  def readpendingfile(self):
    """reads and parses the pending file corresponding to this po file"""
    if os.path.exists(self.pendingfilename):
      pendingmtime = getmodtime(self.pendingfilename)
      if pendingmtime == getattr(self, "pendingmtime", None):
        return
      inputfile = open(self.pendingfilename, "r")
      self.pendingmtime, self.pendingfile = pendingmtime, po.pofile(inputfile, unitclass=self.UnitClass)
      if self.pomtime:
        self.reclassifysuggestions()
    else:
      self.pendingfile = po.pofile(unitclass=self.UnitClass)
      self.savependingfile()

  def savependingfile(self):
    """saves changes to disk..."""
    output = str(self.pendingfile)
    open(self.pendingfilename, "w").write(output)
    self.pendingmtime = getmodtime(self.pendingfilename)

  def readtmfile(self):
    """reads and parses the tm file corresponding to this po file"""
    if os.path.exists(self.tmfilename):
      tmmtime = getmodtime(self.tmfilename)
      if tmmtime == getattr(self, "tmmtime", None):
        return
      inputfile = open(self.tmfilename, "r")
      self.tmmtime, self.tmfile = tmmtime, po.pofile(inputfile, unitclass=self.UnitClass)
    else:
      self.tmfile = po.pofile(unitclass=self.UnitClass)

  def getstats(self):
    """reads the stats if neccessary or returns them from the cache"""
    if os.path.exists(self.statsfilename):
      try:
        self.readstats()
      except Exception, e:
        print "Error reading stats from %s, so recreating (Error was %s)" % (self.statsfilename, e)
        raise
        self.statspomtime = None
    pomtime = getmodtime(self.filename)
    pendingmtime = getmodtime(self.pendingfilename, None)
    if hasattr(self, "pendingmtime"):
      self.readpendingfile()
    lastpomtime = getattr(self, "statspomtime", None)
    lastpendingmtime = getattr(self, "statspendingmtime", None)
    if pomtime is None or pomtime != lastpomtime or pendingmtime != lastpendingmtime:
      self.calcstats()
      self.savestats()
    return self.stats

  def readstats(self):
    """reads the stats from the associated stats file, setting the required variables"""
    statsmtime = getmodtime(self.statsfilename)
    if statsmtime == getattr(self, "statsmtime", None):
      return
    stats = open(self.statsfilename, "r").read()
    mtimes, postatsstring = stats.split("\n", 1)
    mtimes = mtimes.strip().split()
    if len(mtimes) == 1:
      frompomtime = int(mtimes[0])
      frompendingmtime = None
    elif len(mtimes) == 2:
      frompomtime = int(mtimes[0])
      frompendingmtime = int(mtimes[1])
    postats = {}
    msgidwordcounts = []
    msgstrwordcounts = []
    for line in postatsstring.split("\n"):
      if not line.strip():
        continue
      if not ":" in line:
        print "invalid stats line in", self.statsfilename,line
        continue
      name, items = line.split(":", 1)
      if name == "msgidwordcounts":
        msgidwordcounts = [[int(subitem.strip()) for subitem in item.strip().split("/")] for item in items.strip().split(",") if item]
      elif name == "msgstrwordcounts":
        msgstrwordcounts = [[int(subitem.strip()) for subitem in item.strip().split("/")] for item in items.strip().split(",") if item]
      else:
        items = [int(item.strip()) for item in items.strip().split(",") if item]
        postats[name.strip()] = items
    # save all the read times, data simultaneously
    self.statspomtime, self.statspendingmtime, self.statsmtime, self.stats, self.msgidwordcounts, self.msgstrwordcounts = frompomtime, frompendingmtime, statsmtime, postats, msgidwordcounts, msgstrwordcounts
    # if in old-style format (counts instead of items), recalculate
    totalitems = postats.get("total", [])
    if len(totalitems) == 1 and totalitems[0] != 0:
      self.calcstats()
      self.savestats()
    if (len(msgidwordcounts) < len(totalitems)) or (len(msgstrwordcounts) < len(totalitems)):
      self.pofreshen()
      self.countwords()
      self.savestats()

  def savestats(self):
    """saves the current statistics to file"""
    if not os.path.exists(self.filename):
      if os.path.exists(self.statsfilename):
        os.remove(self.statsfilename)
      return
    # assumes self.stats is up to date
    try:
      postatsstring = "\n".join(["%s:%s" % (name, ",".join(map(str,items))) for name, items in self.stats.iteritems()])
      wordcountsstring = "msgidwordcounts:" + ",".join(["/".join(map(str,subitems)) for subitems in self.msgidwordcounts])
      wordcountsstring += "\nmsgstrwordcounts:" + ",".join(["/".join(map(str,subitems)) for subitems in self.msgstrwordcounts])
      statsfile = open(self.statsfilename, "w")
      if os.path.exists(self.pendingfilename):
        statsfile.write("%d %d\n" % (getmodtime(self.filename), getmodtime(self.pendingfilename)))
      else:
        statsfile.write("%d\n" % getmodtime(self.filename))
      statsfile.write(postatsstring + "\n" + wordcountsstring)
      statsfile.close()
    except IOError:
      # TODO: log a warning somewhere. we don't want an error as this is an optimization
      pass
    self.updatequickstats()

  def updatequickstats(self):
    """updates the project's quick stats on this file"""
    translated = self.stats.get("translated")
    fuzzy = self.stats.get("fuzzy")
    translatedwords = sum([sum(self.msgidwordcounts[item]) for item in translated if 0 <= item < len(self.msgidwordcounts)])
    fuzzywords = sum([sum(self.msgidwordcounts[item]) for item in fuzzy if 0 <= item < len(self.msgidwordcounts)])
    totalwords = sum([sum(partcounts) for partcounts in self.msgidwordcounts])
    self.project.updatequickstats(self.pofilename, 
        translatedwords, len(translated), 
        fuzzywords, len(fuzzy), 
        totalwords, len(self.msgidwordcounts))

  def calcstats(self):
    """calculates translation statistics for the given po file"""
    self.pofreshen()
    postats = dict([(name, items) for name, items in self.classify.iteritems()])
    self.stats = postats

  def getassigns(self):
    """reads the assigns if neccessary or returns them from the cache"""
    if os.path.exists(self.assignsfilename):
      self.assigns = self.readassigns()
    else:
      self.assigns = {}
    return self.assigns

  def readassigns(self):
    """reads the assigns from the associated assigns file, returning the assigns
    the format is a number of lines consisting of
    username: action: itemranges
    where itemranges is a comma-separated list of item numbers or itemranges like 3-5
    e.g.  pootlewizz: review: 2-99,101"""
    assignsmtime = getmodtime(self.assignsfilename)
    if assignsmtime == getattr(self, "assignsmtime", None):
      return
    assignsstring = open(self.assignsfilename, "r").read()
    poassigns = {}
    itemcount = len(getattr(self, "classify", {}).get("total", []))
    for line in assignsstring.split("\n"):
      if not line.strip():
        continue
      if not line.count(":") == 2:
        print "invalid assigns line in %s: %r" % (self.assignsfilename, line)
        continue
      username, action, itemranges = line.split(":", 2)
      username, action = username.strip().decode('utf-8'), action.strip().decode('utf-8')
      if not username in poassigns:
        poassigns[username] = {}
      userassigns = poassigns[username]
      if not action in userassigns:
        userassigns[action] = []
      items = userassigns[action]
      for itemrange in itemranges.split(","):
        if "-" in itemrange:
          if not itemrange.count("-") == 1:
            print "invalid assigns range in %s: %r (from line %r)" % (self.assignsfilename, itemrange, line)
            continue
          itemstart, itemstop = [int(item.strip()) for item in itemrange.split("-", 1)]
          items.extend(range(itemstart, itemstop+1))
        else:
          item = int(itemrange.strip())
          items.append(item)
      if itemcount:
        items = [item for item in items if 0 <= item < itemcount]
      userassigns[action] = items
    return poassigns

  def assignto(self, item, username, action):
    """assigns the item to the given username for the given action"""
    userassigns = self.assigns.setdefault(username, {})
    items = userassigns.setdefault(action, [])
    if item not in items:
      items.append(item)
    self.saveassigns()

  def unassign(self, item, username=None, action=None):
    """removes assignments of the item to the given username (or all users) for the given action (or all actions)"""
    if username is None:
      usernames = self.assigns.keys()
    else:
      usernames = [username]
    for username in usernames:
      userassigns = self.assigns.setdefault(username, {})
      if action is None:
        itemlist = [userassigns.get(action, []) for action in userassigns]
      else:
        itemlist = [userassigns.get(action, [])]
      for items in itemlist:
        if item in items:
          items.remove(item)
    self.saveassigns()

  def saveassigns(self):
    """saves the current assigns to file"""
    # assumes self.assigns is up to date
    assignstrings = []
    usernames = self.assigns.keys()
    usernames.sort()
    for username in usernames:
      actions = self.assigns[username].keys()
      actions.sort()
      for action in actions:
        items = self.assigns[username][action]
        items.sort()
        if items:
          lastitem = None
          rangestart = None
          assignstring = "%s: %s: " % (username.encode('utf-8'), action.encode('utf-8'))
          for item in items:
            if item - 1 == lastitem:
              if rangestart is None:
                rangestart = lastitem
            else:
              if rangestart is not None:
                assignstring += "-%d" % lastitem
                rangestart = None
              if lastitem is None:
                assignstring += "%d" % item
              else:
                assignstring += ",%d" % item
            lastitem = item
          if rangestart is not None:
            assignstring += "-%d" % lastitem
          assignstrings.append(assignstring + "\n")
    assignsfile = open(self.assignsfilename, "w")
    assignsfile.writelines(assignstrings)
    assignsfile.close()

  def setmsgstr(self, item, newtarget, userprefs, languageprefs):
    """updates a translation with a new target value"""
    self.pofreshen()
    thepo = self.transelements[item]
    thepo.target = newtarget
    thepo.markfuzzy(False)
    po_revision_date = time.strftime("%F %H:%M%z")
    headerupdates = {"PO_Revision_Date": po_revision_date, "X_Generator": self.x_generator}
    if userprefs:
      if getattr(userprefs, "name", None) and getattr(userprefs, "email", None):
        headerupdates["Last_Translator"] = "%s <%s>" % (userprefs.name, userprefs.email)
    self.updateheader(add=True, **headerupdates)
    if languageprefs:
      nplurals = getattr(languageprefs, "nplurals", None)
      pluralequation = getattr(languageprefs, "pluralequation", None)
      if nplurals and pluralequation:
        self.updateheaderplural(nplurals, pluralequation)
    self.savepofile()
    self.reclassifyelement(item)

  def classifyelements(self):
    """makes a dictionary of which elements fall into which classifications"""
    self.classify = {}
    self.classify["fuzzy"] = []
    self.classify["blank"] = []
    self.classify["translated"] = []
    self.classify["has-suggestion"] = []
    self.classify["total"] = []
    for checkname in self.checker.getfilters().keys():
      self.classify["check-" + checkname] = []
    for item, poel in enumerate(self.transelements):
      classes = poel.classify(self.checker)
      if self.getsuggestions(item):
        classes.append("has-suggestion")
      for classname in classes:
        if classname in self.classify:
          self.classify[classname].append(item)
        else:
          self.classify[classname] = item
    self.countwords()

  def countwords(self):
    """counts the words in each of the elements"""
    self.msgidwordcounts = []
    self.msgstrwordcounts = []
    for poel in self.transelements:
      self.msgidwordcounts.append([wordcount(text) for text in poel.source.strings])
      self.msgstrwordcounts.append([wordcount(text) for text in poel.target.strings])

  def reclassifyelement(self, item):
    """updates the classification of poel in self.classify"""
    poel = self.transelements[item]
    self.msgidwordcounts[item] = [wordcount(text) for text in poel.source.strings]
    self.msgstrwordcounts[item] = [wordcount(text) for text in poel.target.strings]
    classes = poel.classify(self.checker)
    if self.getsuggestions(item):
      classes.append("has-suggestion")
    for classname, matchingitems in self.classify.items():
      if (classname in classes) != (item in matchingitems):
        if classname in classes:
          self.classify[classname].append(item)
        else:
          self.classify[classname].remove(item)
        self.classify[classname].sort()
    self.calcstats()
    self.savestats()

  def reclassifysuggestions(self):
    """shortcut to only update classification of has-suggestion for all items"""
    suggitems = []
    sugglocations = {}
    for thesugg in self.pendingfile.units:
      locations = tuple(thesugg.getlocations())
      sugglocations[locations] = thesugg
    suggitems = [item for item in self.transelements if tuple(item.getlocations()) in sugglocations]
    havesuggestions = self.classify["has-suggestion"]
    for item, poel in enumerate(self.transelements):
      if (poel in suggitems) != (item in havesuggestions):
        if poel in suggitems:
          havesuggestions.append(item)
        else:
          havesuggestions.remove(item)
        havesuggestions.sort()
    self.calcstats()
    self.savestats()

  def getsuggestions(self, item):
    """find all the suggestion items submitted for the given (pofile or pofilename) and item"""
    self.readpendingfile()
    thepo = self.transelements[item]
    locations = thepo.getlocations()
    # TODO: review the matching method
    suggestpos = [suggestpo for suggestpo in self.pendingfile.units if suggestpo.getlocations() == locations]
    return suggestpos

  def addsuggestion(self, item, suggtarget, username):
    """adds a new suggestion for the given item to the pendingfile"""
    self.readpendingfile()
    thepo = self.transelements[item]
    newpo = thepo.copy()
    if username is not None:
      newpo.msgidcomments.append('"_: suggested by %s\\n"' % username)
    newpo.target = suggtarget
    newpo.markfuzzy(False)
    self.pendingfile.units.append(newpo)
    self.savependingfile()
    self.reclassifyelement(item)

  def deletesuggestion(self, item, suggitem):
    """removes the suggestion from the pending file"""
    self.readpendingfile()
    thepo = self.transelements[item]
    locations = thepo.getlocations()
    # TODO: remove the suggestion in a less brutal manner
    pendingitems = [pendingitem for pendingitem, suggestpo in enumerate(self.pendingfile.units) if suggestpo.getlocations() == locations]
    pendingitem = pendingitems[suggitem]
    del self.pendingfile.units[pendingitem]
    self.savependingfile()
    self.reclassifyelement(item)

  def gettmsuggestions(self, item):
    """find all the tmsuggestion items submitted for the given item"""
    self.readtmfile()
    thepo = self.transelements[item]
    locations = thepo.getlocations()
    # TODO: review the matching method
    # Can't simply use the location index, because we want multiple matches
    suggestpos = [suggestpo for suggestpo in self.tmfile.units if suggestpo.getlocations() == locations]
    return suggestpos

  def getitemslen(self):
    """gets the number of items in the file"""
    # TODO: simplify this, and use wherever its needed
    if hasattr(self, "transelements"):
      return len(self.transelements)
    elif hasattr(self, "stats") and "total" in self.stats:
      return len(self.stats["total"])
    elif hasattr(self, "classify") and "total" in self.classify:
      return len(self.classify["total"])
    else:
      # we hadn't read stats...
      return len(self.getstats()["total"])

  def getunassigned(self, action=None):
    """gets all strings that are unassigned (for the given action if given)"""
    unassigneditems = range(0, self.getitemslen())
    assigns = self.getassigns()
    for username in self.assigns:
      if action is not None:
        assigneditems = self.assigns[username].get(action, [])
      else:
        assigneditems = []
        for action, actionitems in self.assigns[username].iteritems():
          assigneditems += actionitems
      unassigneditems = [item for item in unassigneditems if item not in assigneditems]
    return unassigneditems

  def iteritems(self, search, lastitem=None):
    """iterates through the items in this pofile starting after the given lastitem, using the given search"""
    # update stats if required
    self.getstats()
    if lastitem is None:
      minitem = 0
    else:
      minitem = lastitem + 1
    maxitem = len(self.transelements)
    validitems = range(minitem, maxitem)
    if search.assignedto or search.assignedaction: 
      # search.assignedto == [None] means assigned to nobody
      if search.assignedto == [None]:
        assignitems = self.getunassigned(search.assignedaction)
      else:
        # filter based on assign criteria
        self.getassigns()
        if search.assignedto:
          usernames = [search.assignedto]
        else:
          usernames = self.assigns.iterkeys()
        assignitems = []
        for username in usernames:
          if search.assignedaction:
            actionitems = self.assigns[username].get(search.assignedaction, [])
            assignitems.extend(actionitems)
          else:
            for actionitems in self.assigns[username].itervalues():
              assignitems.extend(actionitems)
      validitems = [item for item in validitems if item in assignitems]
    # loop through, filtering on matchnames if required
    for item in validitems:
      if not search.matchnames:
        yield item
      for name in search.matchnames:
        if item in self.classify[name]:
          yield item

  def matchitems(self, newfile, uselocations=False):
    """matches up corresponding items in this pofile with the given newfile, and returns tuples of matching poitems (None if no match found)"""
    if not hasattr(self, "sourceindex"):
      self.makeindex()
    if not hasattr(newfile, "sourceindex"):
      newfile.makeindex()
    matches = []
    for newpo in newfile.units:
      if newpo.isheader():
        continue
      foundid = False
      if uselocations:
        newlocations = newpo.getlocations()
        mergedlocations = []
        for location in newlocations:
          if location in mergedlocations:
            continue
          if location in self.locationindex:
            oldpo = self.locationindex[location]
            if oldpo is not None:
              foundid = True
              matches.append((oldpo, newpo))
              mergedlocations.append(location)
              continue
      if not foundid:
        # We can't use the multistring, because it might contain more than two
        # entries in a PO xliff file. Rather use the singular.
        source = unicode(newpo.source)
        if source in self.sourceindex:
          oldpo = self.sourceindex[source]
          matches.append((oldpo, newpo))
        else:
          matches.append((None, newpo))
    # find items that have been removed
    matcheditems = [oldpo for oldpo, newpo in matches if oldpo]
    for oldpo in self.units:
      if not oldpo in matcheditems:
        matches.append((oldpo, None))
    return matches

  def mergeitem(self, oldpo, newpo, username):
    """merges any changes from newpo into oldpo"""
    unchanged = oldpo.target == newpo.target
#    if oldpo.isblankmsgstr() or newpo.isblankmsgstr() or oldpo.isheader() or newpo.isheader() or unchanged:
    if not oldpo.target or not newpo.target or oldpo.isheader() or newpo.isheader() or unchanged:
      oldpo.merge(newpo)
    else:
      for item, matchpo in enumerate(self.transelements):
        if matchpo == oldpo:
          strings = getattr(newpo.target, "strings", [newpo.target])
          self.addsuggestion(item, strings, username)
          return
      raise KeyError("Could not find item for merge")

  def mergefile(self, newfile, username, allownewstrings=True):
    """make sure each msgid is unique ; merge comments etc from duplicates into original"""
    self.makeindex()
    matches = self.matchitems(newfile)
    for oldpo, newpo in matches:
      if oldpo is None:
        if allownewstrings:
          if isinstance(newpo, po.pounit):
            self.units.append(newpo)
          else:
            self.units.append(self.UnitClass.buildfromunit(newpo))
      elif newpo is None:
        # TODO: mark the old one as obsolete
        pass
      else:
        self.mergeitem(oldpo, newpo, username)
        # we invariably want to get the ids (source locations) from the newpo
        if hasattr(newpo, "sourcecomments"):
          oldpo.sourcecomments = newpo.sourcecomments

    if not isinstance(newfile, po.pofile):
      #TODO: We don't support updating the header yet.
      self.savepofile()
      # the easiest way to recalculate everything
      self.readpofile()
      return

    #Let's update selected header entries. Only the ones listed below, and ones
    #that are empty in self can be updated. The check in header_order is just
    #a basic sanity check so that people don't insert garbage.
    updatekeys = ['Content-Type', 
                  'POT-Creation-Date', 
                  'Last-Translator', 
                  'Project-Id-Version', 
                  'PO-Revision-Date', 
                  'Language-Team']
    headerstoaccept = {}
    ownheader = self.parseheader()
    for (key, value) in newfile.parseheader().items():
      if key in updatekeys or (not key in ownheader or not ownheader[key]) and key in po.poheader.header_order:
        headerstoaccept[key] = value
    self.updateheader(add=True, **headerstoaccept)
    
    #Now update the comments above the header:
    header = self.header()
    newheader = newfile.header()
    if header is None and not newheader is None:
      header = self.UnitClass("", encoding=self.encoding)
      header.target = ""
    if header:  
      header.initallcomments(blankall=True)
      if newheader:
        for i in range(len(header.allcomments)):
          header.allcomments[i].extend(newheader.allcomments[i])
    
    self.savepofile()
    # the easiest way to recalculate everything
    self.readpofile()

class Search:
  """an object containing all the searching information"""
  def __init__(self, dirfilter=None, matchnames=[], assignedto=None, assignedaction=None, searchtext=None):
    self.dirfilter = dirfilter
    self.matchnames = matchnames
    self.assignedto = assignedto
    self.assignedaction = assignedaction
    self.searchtext = searchtext

  def copy(self):
    """returns a copy of this search"""
    return Search(self.dirfilter, self.matchnames, self.assignedto, self.assignedaction, self.searchtext)


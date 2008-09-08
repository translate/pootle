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

"""manages a translation file and its associated files"""

from translate.storage import base
from translate.storage import po
from translate.storage.poheader import tzstring
from translate.storage import xliff
from translate.storage import factory
from translate.filters import checks
from translate.misc.multistring import multistring
from Pootle import __version__
from Pootle import statistics
from jToolkit import timecache
from jToolkit import glock
import time
import os
import bisect
import weakref
import util

_UNIT_CHECKER = checks.UnitChecker()

suggestion_source_index = weakref.WeakKeyDictionary()

def build_map(store, property):
  unit_map = {}
  for unit in store.units:
    key = property(unit)
    if key not in unit_map:
      unit_map[key] = []
    unit_map[key].append(unit)
  return unit_map

def build_index(store, index, property):
  if store not in index:
    index[store] = build_map(store, property)
  return index[store]

def get_source_index(store):
  return build_index(store, suggestion_source_index, lambda unit: unit.source)

class LockedFile:
  """locked interaction with a filesystem file"""
  #Locking is disabled for now since it impacts performance negatively and was
  #not complete yet anyway. Reverse svn revision 5271 to regain the locking
  #code here.
  def __init__(self, filename):
    self.filename = filename
    self.lock = None

  def initlock(self):
    self.lock = glock.GlobalLock(self.filename + os.extsep + "lock")

  def dellock(self):
    del self.lock
    self.lock = None

  def readmodtime(self):
    """returns the modification time of the file (locked operation)"""
    return statistics.getmodtime(self.filename)

  def getcontents(self):
    """returns modtime, contents tuple (locked operation)"""
    pomtime = statistics.getmodtime(self.filename)
    fp = open(self.filename, 'r')
    filecontents = fp.read()
    fp.close()
    return pomtime, filecontents

  def writecontents(self, contents):
    """writes contents to file, returning modification time (locked operation)"""
    f = open(self.filename, 'w')
    f.write(contents)
    f.close()
    pomtime = statistics.getmodtime(self.filename)
    return pomtime

class pootleassigns:
  """this represents the assignments for a file"""
  def __init__(self, basefile):
    """constructs assignments object for the given file"""
    # TODO: try and remove circular references between basefile and this class
    self.basefile = basefile
    self.assignsfilename = self.basefile.filename + os.extsep + "assigns"
    self.getassigns()

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
    assignsmtime = statistics.getmodtime(self.assignsfilename)
    if assignsmtime == getattr(self, "assignsmtime", None):
      return
    assignsfile = open(self.assignsfilename, "r")
    assignsstring = assignsfile.read()
    assignsfile.close()
    poassigns = {}
    itemcount = len(getattr(self, "stats", {}).get("total", []))
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

  def getunassigned(self, action=None):
    """gets all strings that are unassigned (for the given action if given)"""
    unassigneditems = range(0, self.basefile.statistics.getitemslen())
    self.assigns = self.getassigns()
    for username in self.assigns:
      if action is not None:
        assigneditems = self.assigns[username].get(action, [])
      else:
        assigneditems = []
        for action, actionitems in self.assigns[username].iteritems():
          assigneditems += actionitems
      unassigneditems = [item for item in unassigneditems if item not in assigneditems]
    return unassigneditems

  def finditems(self, search):
    """returns items that match the .assignedto and/or .assignedaction criteria in the searchobject"""
    # search.assignedto == [None] means assigned to nobody
    if search.assignedto == [None]:
      assignitems = self.getunassigned(search.assignedaction)
    else:
      # filter based on assign criteria
      assigns = self.getassigns()
      if search.assignedto:
        usernames = [search.assignedto]
      else:
        usernames = assigns.iterkeys()
      assignitems = []
      for username in usernames:
        if search.assignedaction:
          actionitems = assigns[username].get(search.assignedaction, [])
          assignitems.extend(actionitems)
        else:
          for actionitems in assigns[username].itervalues():
            assignitems.extend(actionitems)
    return assignitems

def member(sorted_set, element):
  """Check whether element appears in sorted_set."""
  pos = bisect.bisect_left(sorted_set, element)
  if pos < len(sorted_set):
    return sorted_set[pos] == element
  else:
    return False

def intersect(set_a, set_b):
  """Find the intersection of the sorted sets set_a and set_b."""
  # If both set_a and set_b have elements
  if len(set_b) != 0 and len(set_a) != 0:
    # Find the position of the element in set_a that is at least
    # as large as the minimum element in set_b.
    start_a = bisect.bisect_left(set_a, set_b[0])
    # For each element in set_a...
    for element in set_a[start_a:]:
      # ...which is also in set_b...
      if member(set_b, element):
        yield element

def make_class(base_class):
  class pootlefile(base_class):
    """this represents a pootle-managed file and its associated files"""
    x_generator = "Pootle %s" % __version__.ver
    def __init__(self, project=None, pofilename=None):
      if pofilename:
        self.__class__.__bases__ = (factory.getclass(pofilename),)
      super(pootlefile, self).__init__()
      self.pofilename = pofilename
      if project is None:
        from Pootle import projects
        self.project = projects.DummyProject(None)
        self.checker = None
        self.filename = self.pofilename
      else:
        self.project = project
        self.checker = self.project.checker
        self.filename = os.path.join(self.project.podir, self.pofilename)

      self.lockedfile = LockedFile(self.filename)
      # we delay parsing until it is required
      self.pomtime = None
      self.assigns = None

      self.pendingfilename = self.filename + os.extsep + "pending"
      self.pendingfile = None
      self.pomtime = self.lockedfile.readmodtime()
      self.statistics = statistics.pootlestatistics(self)
      self.tmfilename = self.filename + os.extsep + "tm"
      # we delay parsing until it is required
      self.pomtime = None
      self.tracker = timecache.timecache(20*60)
      self._total = util.undefined # self.statistics.getstats()["total"]

    @util.lazy('_total')
    def _get_total(self):
      return self.statistics.getstats()["total"]

    total = property(_get_total)

    def reset_statistics(self):
      self.statistics = statistics.pootlestatistics(self)

    def parsestring(cls, storestring):
      newstore = cls()
      newstore.parse(storestring)
      return newstore
    parsestring = classmethod(parsestring)

    def parsefile(cls, storefile):
      """Reads the given file (or opens the given filename) and parses back to an object"""
      if isinstance(storefile, basestring):
          storefile = open(storefile, "r")
      if "r" in getattr(storefile, "mode", "r"):
        storestring = storefile.read()
      else:
        storestring = ""
      return cls.parsestring(storestring)
    parsefile = classmethod(parsefile)

    def getheaderplural(self):
      """returns values for nplural and plural values.  It tries to see if the
      file has it specified (in a po header or similar)."""
      try:
        return super(pootlefile, self).getheaderplural()
      except AttributeError:
        return None, None

    def updateheaderplural(self, *args, **kwargs):
      """updates the file header. If there is an updateheader function in the
      underlying store it will be delegated there."""
      try:
        super(pootlefile, self).updateheaderplural(*args, **kwargs)
      except AttributeError:
        pass

    def updateheader(self, **kwargs):
      """updates the file header. If there is an updateheader function in the
      underlying store it will be delegated there."""
      try:
        super(pootlefile, self).updateheader(**kwargs)
      except AttributeError:
        pass

    def readpendingfile(self):
      """reads and parses the pending file corresponding to this file"""
      if os.path.exists(self.pendingfilename):
        inputfile = open(self.pendingfilename, "r")
        self.pendingfile = factory.getobject(inputfile, ignore=".pending")
      else:
        self.pendingfile = po.pofile()

    def savependingfile(self):
      """saves changes to disk..."""
      output = str(self.pendingfile)
      outputfile = open(self.pendingfilename, "w")
      outputfile.write(output)
      outputfile.close()

    def readtmfile(self):
      """reads and parses the tm file corresponding to this file"""
      if os.path.exists(self.tmfilename):
        tmmtime = statistics.getmodtime(self.tmfilename)
        if tmmtime == getattr(self, "tmmtime", None):
          return
        inputfile = open(self.tmfilename, "r")
        self.tmmtime, self.tmfile = tmmtime, factory.getobject(inputfile, ignore=".tm")
      else:
        self.tmfile = po.pofile()

    def getsuggestions(self, item):
      """find all the suggestion items submitted for the given item"""
      unit = self.getitem(item)
      if isinstance(unit, xliff.xliffunit):
        return unit.getalttrans()
      else:
        self.readpendingfile()
        return get_source_index(self.pendingfile).get(unit.source, [])

    def addsuggestion(self, item, suggtarget, username):
      """adds a new suggestion for the given item"""
      unit = self.getitem(item)
      if isinstance(unit, xliff.xliffunit):
        if isinstance(suggtarget, list) and (len(suggtarget) > 0):
          suggtarget = suggtarget[0]
        unit.addalttrans(suggtarget, origin=username)
        self.statistics.reclassifyunit(item)
        self.savepofile()
        return
      self.readpendingfile()
      newpo = unit.copy()
      if username is not None:
        newpo.msgidcomments.append('"_: suggested by %s\\n"' % username)
      newpo.target = suggtarget
      newpo.markfuzzy(False)
      self.pendingfile.addunit(newpo)
      self.savependingfile()
      self.statistics.reclassifyunit(item)

    def deletesuggestion(self, item, suggitem, newtrans=None):
      """removes the suggestion from the pending file"""
      unit = self.getitem(item)
      if hasattr(unit, "xmlelement"):
        suggestions = self.getsuggestions(item)
        unit.delalttrans(suggestions[suggitem])
        self.savepofile()
      else:
        self.readpendingfile()
        # Update the suggestion index
        get_source_index(self.pendingfile)[unit.source] = [unit for unit in get_source_index(self.pendingfile)[unit.source] if unit.target != newtrans]
        # TODO: remove the suggestion in a less brutal manner
        pendingitems = [pendingitem for pendingitem, suggestpo in enumerate(self.pendingfile.units) if suggestpo.target == newtrans]
        try:
          pendingitem = pendingitems[suggitem]
          del self.pendingfile.units[pendingitem]
          self.savependingfile()
        except IndexError:
          pass # TODO: Print a warning for the user.
      self.statistics.reclassifyunit(item)

    def getsuggester(self, item, suggitem):
      """returns who suggested the given item's suggitem if recorded, else None"""
      unit = self.getsuggestions(item)[suggitem]
      if hasattr(unit, "xmlelement"):
        return unit.xmlelement.get("origin")

      for msgidcomment in unit.msgidcomments:
        if msgidcomment.find("suggested by ") != -1:
          suggestedby = po.unquotefrompo([msgidcomment]).replace("_:", "", 1).replace("suggested by ", "", 1).strip()
          return suggestedby
      return None

    def gettmsuggestions(self, item):
      """find all the tmsuggestion items submitted for the given item"""
      self.readtmfile()
      unit = self.getitem(item)
      locations = unit.getlocations()
      # TODO: review the matching method
      # Can't simply use the location index, because we want multiple matches
      suggestpos = [suggestpo for suggestpo in self.tmfile.units if suggestpo.getlocations() == locations]
      return suggestpos

    def track(self, item, message):
      """sets the tracker message for the given item"""
      self.tracker[item] = message

    def readpofile(self):
      """reads and parses the main file"""
      # make sure encoding is reset so it is read from the file
      self.encoding = None
      self.units = []
      self._total = util.undefined
      pomtime, filecontents = self.lockedfile.getcontents()
      # note: we rely on this not resetting the filename, which we set earlier, when given a string
      self.parse(filecontents)
      self.pomtime = pomtime
      self.reset_statistics()

    def savepofile(self, reset_stats=True):
      """saves changes to the main file to disk..."""
      output = str(self)
      self.pomtime = self.lockedfile.writecontents(output)
      if reset_stats:
        self.reset_statistics()
        self.statistics.updatequickstats()

    def pofreshen(self):
      """makes sure we have a freshly parsed pofile

      @return: True if the file was freshened, False otherwise"""
      try:
          if self.pomtime != self.lockedfile.readmodtime():
            self.readpofile()
            return True
      except OSError, e:
          # If this exception is not triggered by a bad
          # symlink, then we have a missing file on our hands...
          if not os.path.islink(self.filename):
              # ...and thus we rescan our files to get rid of the missing filename
              self.project.scanpofiles()
          else:
              print "%s is a broken symlink" % (self.filename,)
      return False

    def getoutput(self):
      """returns pofile output"""
      self.pofreshen()
      return super(pootlefile, self).getoutput()

    def updateunit(self, item, newvalues, userprefs, languageprefs):
      """updates a translation with a new target value"""
      self.pofreshen()
      unit = self.getitem(item)
      reset_stats = False

      if newvalues.has_key("target"):
        unit.target = newvalues["target"]
      if newvalues.has_key("fuzzy"):
        unit.markfuzzy(newvalues["fuzzy"])
      if newvalues.has_key("translator_comments"):
        unit.removenotes()
        if newvalues["translator_comments"]:
          unit.addnote(newvalues["translator_comments"])

      if isinstance(self, po.pofile):
        po_revision_date = time.strftime("%Y-%m-%d %H:%M") + tzstring()
        headerupdates = {"PO_Revision_Date": po_revision_date, "X_Generator": self.x_generator}
        if userprefs:
          if getattr(userprefs, "name", None) and getattr(userprefs, "email", None):
            headerupdates["Last_Translator"] = "%s <%s>" % (userprefs.name, userprefs.email)
        # XXX: If we needed to add a header, the index value in item will be one out after
        # adding the header.
        # TODO: remove once we force the PO class to always output headers
        reset_stats = self.header() is None
        self.updateheader(add=True, **headerupdates)
        if languageprefs:
          nplurals = getattr(languageprefs, "nplurals", None)
          pluralequation = getattr(languageprefs, "pluralequation", None)
          if nplurals and pluralequation:
            self.updateheaderplural(nplurals, pluralequation)
      # If we didn't add a header, savepofile doesn't have to reset the stats,
      # since reclassifyunit will do. This gives us a little speed boost for
      # the common case.
      self.savepofile(reset_stats)
      self.statistics.reclassifyunit(item)

    def getitem(self, item):
      """Returns a single unit based on the item number."""
      return self.units[self.total[item]]

    def iteritems(self, search, lastitem=None):
      """iterates through the items in this pofile starting after the given lastitem, using the given search"""
      def get_min(lastitem):
        if lastitem is None:
          return 0
        else:
          return lastitem + 1

      def narrow_to_last_item_range(translatables, lastitem):
        return translatables[get_min(lastitem):]

      def narrow_to_assigns(translatables, search):
        if search.assignedto or search.assignedaction:
          assignitems = self.getassigns().finditems(search)
          return list(intersect(assignitems, translatables))
        else:
          return translatables

      def narrow_to_matches(translatables, search):
        if search.matchnames:
          stats = self.statistics.getstats()
          matches = reduce(set.__or__, (set(stats[matchname]) for matchname in search.matchnames if matchname in stats))
          return intersect(sorted(matches), translatables)
        else:
          return translatables

      translatables = self.total

      # To get the items to iterate, we
      # 1. filter translatables to the range of elements after lastitem,
      # 2. filter translatables according to assignments,
      # 3. filter translatables according to the quality checks (which
      #    are contained in search.matches)
      new_translatables = narrow_to_matches(
        narrow_to_assigns(
            narrow_to_last_item_range(translatables, lastitem),
            search),
        search)

      # translatables contains the indices into the store of the units. We need to
      # know what indices of these indices are in translatables itself. Since
      # translatables is sorted, we simply need to perform binary searches to
      # get the answer.
      return (bisect.bisect_left(translatables, item) for item in new_translatables)

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
          mergedlocations = set()
          for location in newlocations:
            if location in mergedlocations:
              continue
            if location in self.locationindex:
              oldpo = self.locationindex[location]
              if oldpo is not None:
                foundid = True
                matches.append((oldpo, newpo))
                mergedlocations.add(location)
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
      matcheditems = set(oldpo for oldpo, newpo in matches if oldpo)
      for oldpo in self.units:
        if not oldpo in matcheditems:
          matches.append((oldpo, None))
      return matches

    def getassigns(self):
      if self.assigns is None:
          self.assigns = pootleassigns(self)
      return self.assigns

    def mergeitem(self, po_position, oldpo, newpo, username, suggest=False):
      """merges any changes from newpo into oldpo"""
      unchanged = oldpo.target == newpo.target
      if not suggest and (not oldpo.target or not newpo.target or oldpo.isheader() or newpo.isheader() or unchanged):
        oldpo.merge(newpo)
      else:
        if oldpo in po_position:
          strings = getattr(newpo.target, "strings", [newpo.target])
          self.addsuggestion(po_position[oldpo], strings, username)
        else:
          raise KeyError("Could not find item for merge")

    def mergefile(self, newfile, username, allownewstrings=True, suggestions=False):
      """make sure each msgid is unique ; merge comments etc from duplicates into original"""
      self.makeindex()
      translatables = (self.units[index] for index in self.total)
      po_position = dict((unit, position) for position, unit in enumerate(translatables))
      matches = self.matchitems(newfile)
      for oldpo, newpo in matches:
        if suggestions:
          if oldpo and newpo:
              self.mergeitem(po_position, oldpo, newpo, username, suggest=True)
          continue

        if oldpo is None:
          if allownewstrings:
            self.addunit(self.UnitClass.buildfromunit(newpo))
        elif newpo is None:
          # TODO: mark the old one as obsolete
          pass
        else:
          self.mergeitem(po_position, oldpo, newpo, username)
          # we invariably want to get the ids (source locations) from the newpo
          if hasattr(newpo, "sourcecomments"):
            oldpo.sourcecomments = newpo.sourcecomments

      if not isinstance(newfile, po.pofile) or suggestions:
        #TODO: We don't support updating the header yet.
        self.savepofile()
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
        if key in updatekeys or (not key in ownheader or not ownheader[key]) and key in po.pofile.header_order:
          headerstoaccept[key] = value
      self.updateheader(add=True, **headerstoaccept)

      #Now update the comments above the header:
      header = self.header()
      newheader = newfile.header()
      if header is None and not newheader is None:
        header = self.UnitClass("", encoding=self.encoding)
        header.target = ""
      if header:
        header._initallcomments(blankall=True)
        if newheader:
          for i in range(len(header.allcomments)):
            header.allcomments[i].extend(newheader.allcomments[i])

      self.savepofile()
  return pootlefile

_pootlefile_classes = {}

# We want to extend the functionality of translation stores with some
# Pootle-specific functionality, but we still want them to act like
# translation stores. The clean way to do this, is to store a reference
# to a translation store inside a "pootlefile" class and to delegate
# if needed to the store. This was done initially through __getattr__
# and __setattr__, although it proved to be rather slow (which made
# a difference for large sets of translation files). This is now
# achieved through inheritance. When we have to load a translation file,
# we get hold of its corresponding translation store class. Then we
# see whether there is a class which contains pootlefile functionality
# and which derives from the translation store class. If there isn't
# we invoke make_class to create such a class. Then we return an
# instance of this class to the user.
def pootlefile(project=None, pofilename=None):
  po_class = po.pofile
  if pofilename != None:
    po_class = factory.getclass(pofilename)
  if po_class not in _pootlefile_classes:
    _pootlefile_classes[po_class] = make_class(po_class)
  return _pootlefile_classes[po_class](project, pofilename)

class Search:
  """an object containing all the searching information"""
  def __init__(self, dirfilter=None, matchnames=[], assignedto=None, assignedaction=None, searchtext=None, searchfields=None):
    if searchfields is None:
      searchfields = ["source", "target"]
    self.dirfilter = dirfilter
    self.matchnames = matchnames
    self.assignedto = assignedto
    self.assignedaction = assignedaction
    self.searchtext = searchtext
    self.searchfields = searchfields

  def copy(self):
    """returns a copy of this search"""
    return Search(self.dirfilter, self.matchnames, self.assignedto, self.assignedaction, self.searchtext, self.searchfields)


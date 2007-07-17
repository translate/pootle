import os
from translate.tools import pocount
from translate.storage import statsdb
from translate.filters import checks

def getmodtime(filename, default=None):
  """gets the modificationtime of the given file"""
  if os.path.exists(filename):
    return os.stat(filename)[os.path.stat.ST_MTIME]
  else:
    return default

class StatsFile:
  """Manages a statistics data file"""
  def __init__(self, basefile):
    self.basefile = basefile
    self.refname = self.basefile.filename
    self.filename = self.refname + os.extsep + "stats"

  def read(self):
    """return the contents of the stats file"""
    sfile =  open(self.filename, "r")
    contents = sfile.read()
    sfile.close()
    return contents

  def save(self, statsstring):
    """save the stats data"""
    sfile = open(self.filename, "w")
    if os.path.exists(self.basefile.pendingfilename):
      sfile.write("%d %d\n" % (getmodtime(self.basefile.filename), getmodtime(self.basefile.pendingfilename)))
    else:
      sfile.write("%d\n" % getmodtime(self.basefile.filename))
    sfile.write(statsstring)
    sfile.close()

  def hasparent(self):
    """check if the stats file has a parent data file, if not delete it"""
    if os.path.exists(self.basefile.filename):
      return True
    else:
      if os.path.exists(self.filename):
        os.remove(self.filename)
      return False

class pootlestatistics:
  """this represents the statistics known about a file"""
  def __init__(self, basefile, generatestats=True):
    """constructs statistic object for the given file"""
    # TODO: try and remove circular references between basefile and this class
    self.basefile = basefile
    self.sfile = StatsFile(self.basefile)
    self.classify = {}
    self.sourcewordcounts = []
    self.targetwordcounts = []
    if generatestats:
      self.getstats()

  def getstats(self):
    """reads the stats if neccessary or returns them from the cache"""
    if os.path.exists(self.sfile.filename):
      try:
        self.readstats()
      except Exception, e:
        print "Error reading stats from %s, so recreating (Error was %s)" % (self.sfile.filename, e)
        self.statspomtime = None
        raise
    pomtime = getmodtime(self.basefile.filename)
    pendingmtime = getmodtime(self.basefile.pendingfilename, None)
    if hasattr(self, "pendingmtime"):
      self.basefile.readpendingfile()
    lastpomtime = getattr(self, "statspomtime", None)
    lastpendingmtime = getattr(self, "statspendingmtime", None)
    if pomtime is None or pomtime != lastpomtime or pendingmtime != lastpendingmtime:
      self.calcstats()
      self.savestats()
    return self.stats

  def readstats(self):
    """reads the stats from the associated stats file, setting the required variables"""
    statsmtime = getmodtime(self.sfile.filename)
    if statsmtime == getattr(self, "statsmtime", None):
      return
    stats = self.sfile.read()
    mtimes, statsstring = stats.split("\n", 1)
    mtimes = mtimes.strip().split()
    if len(mtimes) == 1:
      frompomtime = int(mtimes[0])
      frompendingmtime = None
    elif len(mtimes) == 2:
      frompomtime = int(mtimes[0])
      frompendingmtime = int(mtimes[1])
    stats = {}
    for line in statsstring.split("\n"):
      if not line.strip():
        continue
      if not ":" in line:
        print "invalid stats line in", self.sfile.filename,line
        continue
      name, items = line.split(":", 1)
      if name == "msgidwordcounts" or name == "sourcewordcounts":
        stats["sourcewordcounts"] = [[int(subitem.strip()) for subitem in item.strip().split("/")] for item in items.strip().split(",") if item]
      elif name == "msgstrwordcounts" or name == "targetwordcounts":
        stats["targetwordcounts"] = [[int(subitem.strip()) for subitem in item.strip().split("/")] for item in items.strip().split(",") if item]
      else:
        items = [int(item.strip()) for item in items.strip().split(",") if item]
        stats[name.strip()] = items
    # save all the read times, data simultaneously
    self.statspomtime, self.statspendingmtime, self.statsmtime, self.stats, self.sourcewordcounts, self.targetwordcounts = frompomtime, frompendingmtime, statsmtime, stats, stats["sourcewordcounts"], stats["targetwordcounts"]
    # if in old-style format (counts instead of items), recalculate
    totalitems = stats.get("total", [])
    if len(totalitems) == 1 and totalitems[0] != 0:
      self.calcstats()
      self.savestats()
    if (len(stats["sourcewordcounts"]) < len(totalitems)) or (len(stats["targetwordcounts"]) < len(totalitems)):
      self.basefile.pofreshen()
      self.countwords()
      self.savestats()

  def savestats(self):
    """saves the current statistics to file"""
    if not self.sfile.hasparent():
      return
    # assumes self.stats is up to date
    try:
      statsstring = "\n".join(["%s:%s" % (name, ",".join(map(str,items))) for name, items in self.stats.iteritems()])
      wordcountsstring = "sourcewordcounts:" + ",".join(["/".join(map(str,subitems)) for subitems in self.sourcewordcounts])
      wordcountsstring += "\ntargetwordcounts:" + ",".join(["/".join(map(str,subitems)) for subitems in self.targetwordcounts])
      self.sfile.save(statsstring + "\n" + wordcountsstring)
    except IOError:
      # TODO: log a warning somewhere. we don't want an error as this is an optimization
      pass
    self.updatequickstats()

  def updatequickstats(self):
    """updates the project's quick stats on this file"""
    translated = self.stats.get("translated")
    fuzzy = self.stats.get("fuzzy")
    translatedwords = sum([sum(self.sourcewordcounts[item]) for item in translated if 0 <= item < len(self.sourcewordcounts)])
    fuzzywords = sum([sum(self.sourcewordcounts[item]) for item in fuzzy if 0 <= item < len(self.sourcewordcounts)])
    totalwords = sum([sum(partcounts) for partcounts in self.sourcewordcounts])
    self.basefile.project.updatequickstats(self.basefile.pofilename, 
        translatedwords, len(translated), 
        fuzzywords, len(fuzzy), 
        totalwords, len(self.sourcewordcounts))

  def calcstats(self):
    """calculates translation statistics for the given file"""
    # handle this being called when self.basefile.statistics is being set and calcstats is called from self.__init__
    if not hasattr(self.basefile, "statistics"):
      self.basefile.statistics = self
    self.basefile.pofreshen()
    self.stats = dict([(name, items) for name, items in self.classify.iteritems()])

  def classifyunit(self, unit):
    """returns all classify keys that the unit should match"""
    classes = ["total"]
    if unit.isfuzzy():
      classes.append("fuzzy")
    if unit.gettargetlen() == 0:
      classes.append("blank")
    if unit.istranslated():
      classes.append("translated")
    # TODO: we don't handle checking plurals at all yet, as this is tricky...
    source = unit.source
    target = unit.target
    if isinstance(source, str) and isinstance(target, unicode):
      source = source.decode(getattr(unit, "encoding", "utf-8"))
    checkresult = self.basefile.checker.run_filters(unit, source, target)
    for checkname, checkmessage in checkresult:
      classes.append("check-" + checkname)
    return classes

  def classifyunits(self):
    """makes a dictionary of which units fall into which classifications"""
    self.classify = {}
    self.classify["fuzzy"] = []
    self.classify["blank"] = []
    self.classify["translated"] = []
    self.classify["has-suggestion"] = []
    self.classify["total"] = []
    for checkname in self.basefile.checker.getfilters().keys():
      self.classify["check-" + checkname] = []
    for item, unit in enumerate(self.basefile.transunits):
      classes = self.classifyunit(unit)
      if self.basefile.getsuggestions(item):
        classes.append("has-suggestion")
      for classname in classes:
        if classname in self.classify:
          self.classify[classname].append(item)
        else:
          self.classify[classname] = item
    self.countwords()

  def countwords(self):
    """counts the words in each of the units"""
    self.sourcewordcounts = []
    self.targetwordcounts = []
    for unit in self.basefile.transunits:
      self.sourcewordcounts.append([statsdb.wordcount(text) for text in unit.source.strings])
      self.targetwordcounts.append([statsdb.wordcount(text) for text in unit.target.strings])

  def reclassifyunit(self, item):
    """updates the classification of a unit in self.classify"""
    unit = self.basefile.transunits[item]
    self.sourcewordcounts[item] = [statsdb.wordcount(text) for text in unit.source.strings]
    self.targetwordcounts[item] = [statsdb.wordcount(text) for text in unit.target.strings]
    classes = self.classifyunit(unit)
    if self.basefile.getsuggestions(item):
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

  def getitemslen(self):
    """gets the number of items in the file"""
    # TODO: simplify this, and use wherever its needed
    if hasattr(self.basefile, "transunits"):
      return len(self.basefile.transunits)
    elif hasattr(self, "stats") and "total" in self.stats:
      return len(self.stats["total"])
    elif hasattr(self, "classify") and "total" in self.classify:
      return len(self.classify["total"])
    else:
      # we hadn't read stats...
      return len(self.getstats()["total"])

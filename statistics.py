from translate.storage import statsdb

STATS_DB_FILE = None

def getmodtime(filename):
  try:
    mtime, _size = statsdb.get_mod_info(filename)
    return mtime
  except:
    return None

def memoize(f):
  def memoized_f(self, *args, **kwargs):
    f_name = f.__name__
    table = self._memoize_table
    if f_name not in table:
      table[f_name] = f(self, *args, **kwargs)
    return table[f_name]
  return memoized_f

class pootlestatistics:
  """this represents the statistics known about a file"""
  def __init__(self, basefile):
    """constructs statistic object for the given file"""
    # TODO: try and remove circular references between basefile and this class
    self.basefile = basefile
    self._stats = None
    self._totals = None
    self._unitstats = None
    self.statscache = statsdb.StatsCache(STATS_DB_FILE)
    self._memoize_table = {}

  @memoize
  def getquickstats(self):
    """returns the quick statistics (totals only)"""
    try:
      return self.statscache.filetotals(self.basefile.filename)
    except:
      return statsdb.emptyfiletotals()
    
  @memoize
  def getstats(self, checker=None):
    """reads the stats if neccessary or returns them from the cache"""
    if checker == None:
      checker = self.basefile.checker
    try:
      return self.statscache.filestats(self.basefile.filename, checker)
    except:
      return statsdb.emptystats()

  @memoize
  def getunitstats(self):
    try:
      return self.statscache.unitstats(self.basefile.filename)
    except:
      return statsdb.emptyunitstats()

  def updatequickstats(self, save=True):
    """updates the project's quick stats on this file"""
    totals = self.getquickstats()
    self.basefile.project.updatequickstats(self.basefile.pofilename, 
        totals.get("translatedsourcewords", 0), totals.get("translated", 0),
        totals.get("fuzzysourcewords", 0), totals.get("fuzzy", 0),
        totals.get("totalsourcewords", 0), totals.get("total", 0),
        save)

  def reclassifyunit(self, item):
    """Reclassifies all the information in the database and self._stats about 
    the given unit"""
    unit = self.basefile.getitem(item)
    item = self.getstats()["total"][item]
    
    classes = self.statscache.recacheunit(self.basefile.filename, self.basefile.checker, unit)
    for classname, matchingitems in self.getstats().items():
      if (classname in classes) != (item in matchingitems):
        if classname in classes:
          self.getstats()[classname].append(item)
        else:
          self.getstats()[classname].remove(item)
        self.getstats()[classname].sort()
    self.updatequickstats()

  @memoize
  def getitemslen(self):
    """gets the number of items in the file"""
    return self.getquickstats()["total"]

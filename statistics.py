import os
from translate.storage import statsdb
from translate.filters import checks
from translate.misc.multistring import multistring

STATS_DB_FILE = None

def getmodtime(filename):
    mtime, size = statsdb.get_mod_info(filename, errors_return_empty=True, empty_return=None)
    return mtime

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

  def getquickstats(self):
    """returns the quick statistics (totals only)"""
    if not self._totals:
      self._totals = self.statscache.filetotals(self.basefile.filename, errors_return_empty=True)
    return self._totals

  def getstats(self, checker=None):
    """reads the stats if neccessary or returns them from the cache"""
    if checker == None:
        checker = self.basefile.checker
    if not self._stats:
      self._stats = self.statscache.filestats(self.basefile.filename, checker, errors_return_empty=True)
    return self._stats
  
  def purge_totals(self):
    """Temporary helper to clean up where needed. We might be able to remove 
    this after the move to cpo."""
    self._totals = None
    self._stats = None
    self._unitstats = None

  def getunitstats(self):
    if not self._unitstats:
      self._unitstats = self.statscache.unitstats(self.basefile.filename, errors_return_empty=True)
    return self._unitstats

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
    # We should be doing better, but for now it is easiet to simply force a 
    # reload from the database
    self.purge_totals()

  def getitemslen(self):
    """gets the number of items in the file"""
    return self.getquickstats()["total"]

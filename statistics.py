import request_cache
import traceback

STATS_OPTIONS = {} 

def getmodtime(filename):
  try:
    mtime, _size = statsdb.get_mod_info(filename)
    return mtime
  except:
    return None

_complaint_status = set()

def _complain(message, filename):
  if filename not in _complaint_status:
    print message % filename
    _complaint_status.add(filename)
    traceback.print_exc()

class pootlestatistics:
  """this represents the statistics known about a file"""
  def __init__(self, basefile):
    """constructs statistic object for the given file"""
    # TODO: try and remove circular references between basefile and this class
    self.basefile = basefile
    self.statscache = statsdb.StatsCache(STATS_OPTIONS['database'])

  def getquickstats(self):
    """returns the quick statistics (totals only)"""
    try:
      return request_cache.call(self.statscache.filetotals, self.basefile.filename) or statsdb.emptyfiletotals()
    except:
      _complain(u'Could not compute file totals for %s', self.basefile.filename)
      return statsdb.emptyfiletotals()

  def getstats(self, checker=None):
    """reads the stats if neccessary or returns them from the cache"""
    if checker == None:
      checker = self.basefile.checker
    try:
      return request_cache.call(self.statscache.filestats, self.basefile.filename, checker)
    except:
      _complain(u'Could not compute statistics for %s', self.basefile.filename)
      return statsdb.emptyfilestats()

  def getunitstats(self):
    try:
      return request_cache.call(self.statscache.unitstats, self.basefile.filename)
    except:
      _complain(u'Could not compute word counts for %s', self.basefile.filename)
      return statsdb.emptyunitstats()

  def reclassifyunit(self, item):
    """Reclassifies all the information in the database and self._stats about
    the given unit"""
    unit = self.basefile.getitem(item)
    self.statscache.recacheunit(self.basefile.filename, self.basefile.checker, unit)
    self._memoize_table = {}

  def getitemslen(self):
    """gets the number of items in the file"""
    return self.getquickstats()["total"]

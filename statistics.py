#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2009 Zuza Software Foundation
#
# This file is part of Pootle.
#
# Pootle is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# Pootle is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Pootle; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from django.conf import settings

from translate.storage import statsdb

import traceback

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
    self.statscache = statsdb.StatsCache(settings.STATS_DB_PATH)

  def getquickstats(self):
    """returns the quick statistics (totals only)"""
    try:
      return self.statscache.filetotals(self.basefile.filename) or statsdb.emptyfiletotals()
    except:
      _complain(u'Could not compute file totals for %s', self.basefile.filename)
      return statsdb.emptyfiletotals()

  def getstats(self, checker=None):
    """reads the stats if neccessary or returns them from the cache"""
    if checker == None:
      checker = self.basefile.checker
    try:
      return self.statscache.filestats(self.basefile.filename, checker)
    except:
      _complain(u'Could not compute statistics for %s', self.basefile.filename)
      return statsdb.emptyfilestats()

  def getunitstats(self):
    try:
      return self.statscache.unitstats(self.basefile.filename)
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

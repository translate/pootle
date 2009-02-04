#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""class for caching objects with timed expiry"""

# Copyright 2002, 2003 St James Software
# 
# This file is part of jToolkit.
#
# jToolkit is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
# 
# jToolkit is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with jToolkit; if not, write to the Free Software
# Foundation, Inc., 59 Temple Place, Suite 330, Boston, MA  02111-1307  USA

from Pootle.legacy.jToolkit.data import dates

class timecache(dict):
  """caches objects, remembers time, and dumps when neccessary..."""
  def __init__(self, expiryperiod):
    """constructs a timecache dictionary with an expiryperiod given in seconds..."""
    dict.__init__(self)
    self.expiryperiod = dates.seconds(expiryperiod)

  def expired(self, timestamp):
    """checks if self.timestamp is older than self.expiryperiod"""
    return timestamp < self.gettimestamp() - self.expiryperiod

  def expire(self, key):
    """expires the key, removing the associated item"""
    self.__delitem__(key)

  def gettimestamp(self):
    """returns a new timestamp for the current time..."""
    return dates.currentdate()

  def purge(self):
    """removes all items that are older then self.expiryperiod"""
    keystodelete = []
    for key, (timestamp, value) in dict.iteritems(self):
      if self.expired(timestamp):
        keystodelete.append(key)
    for key in keystodelete:
      self.expire(key)

  def __contains__(self, key):
    """in operator"""
    if dict.__contains__(self, key):
      timestamp, value = dict.__getitem__(self, key)
      if self.expired(timestamp):
        self.expire(key)
        # this allows expire to actually reset the value
        return dict.__contains__(self, key)
      return 1
    return 0

  def __getitem__(self, key):
    """[] access of items"""
    timestamp, value = dict.__getitem__(self, key)
    if self.expired(timestamp):
      self.expire(key)
      # this allows expire to actually reset the value
      if dict.__contains__(self, key):
        return dict.__getitem__(self, key)[1]
      raise KeyError, key
    return value

  def __iter__(self):
    """iterator access of items"""
    self.purge()
    return dict.__iter__(self)

  def __repr__(self):
    """x.__repr__() <==> repr(x)"""
    self.purge()
    return repr(dict(self.items()))

  def __setitem__(self, key, value):
    """[] setting of items"""
    timestamp = self.gettimestamp()
    dict.__setitem__(self, key, (timestamp, value))

  def has_key(self, key):
    """check if key is present"""
    return self.__contains__(key)

  def get(self, key, default=None):
    """D.get(k[,d]) -> D[k] if D.has_key(k), else d.  d defaults to None."""
    timestamp, value = dict.get(self, key, (None, default))
    if timestamp is None:
      return value
    elif self.expired(timestamp):
      self.expire(key)
      # this allows expire to actually reset the value
      return dict.get(self, key, (None, default))[1]
    return value

  def items(self):
    """D.items() -> list of D's (key, value) pairs, as 2-tuples"""
    self.purge()
    return [(key, value) for (key, (timestamp, value)) in dict.items(self)]

  def iteritems(self):
    """D.iteritems() -> an iterator over the (key, value) items of D"""
    self.purge()
    for key, (timestamp, value) in dict.iteritems(self):
      yield (key, value)

  def iterkeys(self):
    """D.iterkeys() -> an iterator over the keys of D"""
    self.purge()
    return dict.iterkeys(self)

  def itervalues(self):
    """D.itervalues() -> an iterator over the values of D"""
    self.purge()
    for timestamp, value in dict.itervalues(self):
      yield value

  def keys(self):
    """D.keys() -> list of D's keys"""
    self.purge()
    return dict.keys(self)

  def values(self):
    """D.values() -> list of D's values"""
    self.purge()
    return [value for (timestamp, value) in dict.values(self)]

  def popitem(self):
    """D.popitem() -> (k, v), remove and return some (key, value) pair as a
    2-tuple; but raise KeyError if D is empty"""
    self.purge()
    key, (timestamp, value) = dict.popitem(self)
    return (key, value)

  def setdefault(self, key, failobj=None):
    """D.setdefault(k[,d]) -> D.get(k,d), also set D[k]=d if k not in D"""
    newtimestamp = self.gettimestamp()
    oldtimestamp, value = dict.setdefault(self, key, (newtimestamp, failobj))
    if self.expired(oldtimestamp):
      dict.__setitem__(self, key, (newtimestamp, failobj))
      return failobj
    return value

  def update(self, updatedict):
    """D.update(E) -> None.  Update D from E: for k in E.keys(): D[k] = E[k]"""
    for key in updatedict.keys():
      self[key] = updatedict[key]


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
#
# Derived from Raymond Hettinger's recipe at 
# http://code.activestate.com/recipes/498245/

from collections import deque

class LRUCache(object):
    def __init__(self, maxsize, maker):
        self.cache = {}              # mapping of key to results
        self.queue = deque()         # order that keys have been accessed
        self.refcount = {}           # number of times each key is in the access queue
        self.maxsize = maxsize
        self.maker = maker

    def _compact_cache(self):
        # Periodically compact the queue by duplicate keys
        if len(self.queue) > self.maxsize * 4:
            for i in xrange(len(self.queue)):
                k = self.queue.popleft()
                if self.refcount[k] == 1:
                    self.queue.append(k)
                else:
                    self.refcount[k] -= 1

    def _purge_cache(self):
        # Purge least recently accessed cache contents
        while len(self.cache) > self.maxsize:
            k = self.queue.popleft()
            self.refcount[k] -= 1
            if not self.refcount[k]:
                del self.cache[k]
                del self.refcount[k]
        self._compact_cache()
        
    def _reference(self, key):
        self.queue.append(key)
        self.refcount[key] = self.refcount.get(key, 0) + 1

    def __getitem__(self, key):
        # get cache entry or compute if not found
        try:
            result = self.cache[key]
        except KeyError:
            result = self.cache[key] = self.maker(key)

        # record that this key was recently accessed
        self._reference(key)
        self._purge_cache()
        return result

    def __setitem__(self, key, value):
        self.cache[key] = value
        self._reference(key)
        self._purge_cache()



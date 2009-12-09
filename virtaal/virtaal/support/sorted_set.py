#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# Copyright 2007-2008 Zuza Software Foundation
#
# This file is part of Virtaal.
# The file was taken from
# http://aspn.activestate.com/ASPN/Cookbook/Python/Recipe/230113
# and was written by Raymond Hettinger.
#
# This program is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, see <http://www.gnu.org/licenses/>.

""" altsets.py -- An alternate implementation of Sets.py

Implements set operations using sorted lists as the underlying data structure.

Advantages:

  - Space savings -- lists are much more compact than a dictionary
    based implementation.

  - Flexibility -- elements do not need to be hashable, only __cmp__
    is required.

  - Fast operations depending on the underlying data patterns.
    Non-overlapping sets get united, intersected, or differenced
    with only log(N) element comparisons.  Results are built using
    fast-slicing.

  - Algorithms are designed to minimize the number of compares
    which can be expensive.

  - Natural support for sets of sets.  No special accomodation needs to
    be made to use a set or dict as a set member, but users need to be
    careful to not mutate a member of a set since that may breaks its
    sort invariant.

Disadvantages:

  - Set construction uses list.sort() with potentially N log(N)
    comparisons.

  - Membership testing and element addition use log(N) comparisons.
    Element addition uses list.insert() with takes O(N) time.

ToDo:

   - Make the search routine adapt to the data; falling backing to
     a linear search when encountering random data.

"""

from bisect import bisect_left

import gobject


class SortedSet(gobject.GObject):
    __gtype_name__ = "SortedSet"

    __gsignals__ = {
        "removed":       (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_PYOBJECT)),
        "added":         (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_PYOBJECT)),
        "before-remove": (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_PYOBJECT)),
        "before-add":    (gobject.SIGNAL_RUN_FIRST, gobject.TYPE_NONE, (gobject.TYPE_INT, gobject.TYPE_PYOBJECT))
    }

    def __init__(self, iterable):
        gobject.GObject.__init__(self)

        data = list(iterable)
        data.sort()
        result = data[:1]
        for elem in data[1:]:
            if elem == result[-1]:
                continue
            result.append(elem)
        self.data = result

    def __repr__(self):
        return 'SortedSet(' + repr(self.data) + ')'

    def __iter__(self):
        return iter(self.data)

    def __contains__(self, elem):
        data = self.data
        i = bisect_left(self.data, elem, 0)
        return i<len(data) and data[i] == elem

    def add(self, elem):
        if elem not in self:
            i = bisect_left(self.data, elem)
            self.emit('before-add', i, elem)
            self.data.insert(i, elem)
            self.emit('added', i, elem)

    def remove(self, elem):
        data = self.data
        i = bisect_left(self.data, elem, 0)
        if i<len(data) and data[i] == elem:
            elem = data[i]
            self.emit('before-remove', i, elem)
            del data[i]
            self.emit('removed', i, elem)

    def _getotherdata(other):
        if not isinstance(other, SortedSet):
            other = SortedSet(other)
        return other.data
    _getotherdata = staticmethod(_getotherdata)

    def __cmp__(self, other, cmp=cmp):
        return cmp(self.data, SortedSet._getotherdata(other))

    def union(self, other, find=bisect_left):
        i = j = 0
        x = self.data
        y = SortedSet._getotherdata(other)
        result = SortedSet([])
        append = result.data.append
        extend = result.data.extend
        try:
            while 1:
                if x[i] == y[j]:
                    append(x[i])
                    i += 1
                    j += 1
                elif x[i] > y[j]:
                    cut = find(y, x[i], j)
                    extend(y[j:cut])
                    j = cut
                else:
                    cut = find(x, y[j], i)
                    extend(x[i:cut])
                    i = cut
        except IndexError:
            extend(x[i:])
            extend(y[j:])
        return result

    def intersection(self, other, find=bisect_left):
        i = j = 0
        x = self.data
        y = SortedSet._getotherdata(other)
        result = SortedSet([])
        append = result.data.append
        try:
            while 1:
                if x[i] == y[j]:
                    append(x[i])
                    i += 1
                    j += 1
                elif x[i] > y[j]:
                    j = find(y, x[i], j)
                else:
                    i = find(x, y[j], i)
        except IndexError:
            pass
        return result

    def difference(self, other, find=bisect_left):
        i = j = 0
        x = self.data
        y = SortedSet._getotherdata(other)
        result = SortedSet([])
        extend = result.data.extend
        try:
            while 1:
                if x[i] == y[j]:
                    i += 1
                    j += 1
                elif x[i] > y[j]:
                    j = find(y, x[i], j)
                else:
                    cut = find(x, y[j], i)
                    extend(x[i:cut])
                    i = cut
        except IndexError:
            extend(x[i:])
        return result

    def symmetric_difference(self, other, find=bisect_left):
        i = j = 0
        x = self.data
        y = SortedSet._getotherdata(other)
        result = SortedSet([])
        extend = result.data.extend
        try:
            while 1:
                if x[i] == y[j]:
                    i += 1
                    j += 1
                elif x[i] > y[j]:
                    cut = find(y, x[i], j)
                    extend(y[j:cut])
                    j = cut
                else:
                    cut = find(x, y[j], i)
                    extend(x[i:cut])
                    i = cut
        except IndexError:
            extend(x[i:])
            extend(y[j:])
        return result
